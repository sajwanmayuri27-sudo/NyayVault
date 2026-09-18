"""
Lightweight blockchain anchoring layer.

Purpose: take a file's SHA-256 hash (already computed by
app/utils/hashing.py at upload time) and register it on a local/testnet
smart contract via web3.py, so a tamper-check can later be corroborated
against an immutable, third-party-verifiable record -- independent of our
own database.

Design constraints this module respects:
  - The database remains the single source of truth for actual storage and
    queries. This module does exactly one thing: send a hash to a chain and
    hand back the transaction hash. It never reads/writes case or document
    rows itself -- callers (see app/routers/documents.py) own that.
  - web3.py is imported lazily, inside functions, not at module import time.
    If it isn't installed, or `BLOCKCHAIN_ANCHORING_ENABLED` is left off (the
    default), importing this module -- and importing the rest of the app --
    still works with zero setup, exactly as before this feature existed.
  - Every failure mode (no node running, bad private key, no contract
    deployed, insufficient gas funds, etc.) raises a clear, typed exception
    instead of hanging or crashing the caller. Callers are expected to run
    this in a background task and treat failures as non-fatal to the upload
    itself (see documents.py).

Deploying the contract
-----------------------
A minimal Solidity source for the expected contract lives alongside this
file at app/utils/contracts/HashAnchor.sol. Deploy it to any local/testnet
chain (Ganache, Anvil, Hardhat node, Sepolia, etc.) with Remix, Hardhat, or
Foundry, then set these env vars (see .env.example):

    BLOCKCHAIN_ANCHORING_ENABLED=true
    BLOCKCHAIN_RPC_URL=http://127.0.0.1:8545
    BLOCKCHAIN_CHAIN_ID=1337
    BLOCKCHAIN_PRIVATE_KEY=0x...        # a dev/test account's key only
    BLOCKCHAIN_CONTRACT_ADDRESS=0x...   # address HashAnchor was deployed to

The contract's `anchorHash(bytes32)` stores (sender, block.timestamp)
keyed by the hash and emits a `HashAnchored` event; `isAnchored(bytes32)`
and `getRecord(bytes32)` are free (read-only) calls anyone can use to
independently verify a hash was anchored, without trusting this API.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from app.config import settings

# ABI for app/utils/contracts/HashAnchor.sol. Kept in sync by hand since the
# contract is intentionally tiny and stable -- if you change the .sol file,
# update this to match (or generate it with solc/Hardhat and paste it here).
CONTRACT_ABI = [
    {
        "inputs": [{"internalType": "bytes32", "name": "fileHash", "type": "bytes32"}],
        "name": "anchorHash",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "fileHash", "type": "bytes32"}],
        "name": "isAnchored",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "fileHash", "type": "bytes32"}],
        "name": "getRecord",
        "outputs": [
            {"internalType": "address", "name": "anchoredBy", "type": "address"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "fileHash", "type": "bytes32"},
            {"indexed": True, "internalType": "address", "name": "anchoredBy", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"},
        ],
        "name": "HashAnchored",
        "type": "event",
    },
]


class BlockchainAnchorError(Exception):
    """Raised for any anchoring failure: disabled, misconfigured, node
    unreachable, transaction rejected, etc. Always safe to catch broadly
    and treat as non-fatal by callers that must not block on-chain issues."""


class AlreadyAnchoredError(BlockchainAnchorError):
    """Raised when the contract already has a record for this exact hash
    (HashAnchor.sol rejects duplicate anchors). Not really a failure --
    the hash is provably on-chain already -- but there's no *new*
    transaction hash to report, so it's surfaced distinctly."""


@dataclass(frozen=True)
class AnchorRecord:
    anchored_by: str
    timestamp: int
    exists: bool


def _require_web3():
    try:
        from web3 import Web3
    except ImportError as exc:
        raise BlockchainAnchorError(
            "web3.py is not installed. Run `pip install web3` (see requirements.txt)."
        ) from exc
    return Web3


@lru_cache(maxsize=1)
def _get_web3():
    """Builds (and caches) a single Web3 connection for the process. Cached
    so every anchoring call doesn't re-handshake with the node -- this is
    the only part of the module that's shared/reused across calls."""
    Web3 = _require_web3()

    if not settings.BLOCKCHAIN_ANCHORING_ENABLED:
        raise BlockchainAnchorError(
            "Blockchain anchoring is disabled (set BLOCKCHAIN_ANCHORING_ENABLED=true)."
        )
    if not settings.BLOCKCHAIN_RPC_URL:
        raise BlockchainAnchorError("BLOCKCHAIN_RPC_URL is not configured.")

    w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_RPC_URL))
    try:
        connected = w3.is_connected()
    except Exception as exc:  # noqa: BLE001 - node might be down, DNS fail, etc.
        raise BlockchainAnchorError(
            f"Could not reach blockchain node at {settings.BLOCKCHAIN_RPC_URL}: {exc}"
        ) from exc
    if not connected:
        raise BlockchainAnchorError(
            f"Blockchain node at {settings.BLOCKCHAIN_RPC_URL} is not responding."
        )
    return w3


def _get_contract():
    if not settings.BLOCKCHAIN_CONTRACT_ADDRESS:
        raise BlockchainAnchorError(
            "BLOCKCHAIN_CONTRACT_ADDRESS is not configured -- deploy HashAnchor.sol "
            "and set its address first."
        )
    w3 = _get_web3()
    try:
        address = w3.to_checksum_address(settings.BLOCKCHAIN_CONTRACT_ADDRESS)
    except AttributeError:
        # web3.py v5 fallback (v6+ uses the snake_case name above).
        address = w3.toChecksumAddress(settings.BLOCKCHAIN_CONTRACT_ADDRESS)
    return w3.eth.contract(address=address, abi=CONTRACT_ABI)


def _hash_to_bytes32(sha256_hex: str) -> bytes:
    cleaned = sha256_hex[2:] if sha256_hex.startswith("0x") else sha256_hex
    try:
        raw = bytes.fromhex(cleaned)
    except ValueError as exc:
        raise BlockchainAnchorError(f"'{sha256_hex}' is not valid hex.") from exc
    if len(raw) != 32:
        raise BlockchainAnchorError(
            f"Expected a 32-byte SHA-256 hash, got {len(raw)} bytes."
        )
    return raw


def _sign_and_send(w3, tx: dict) -> str:
    signed = w3.eth.account.sign_transaction(tx, private_key=settings.BLOCKCHAIN_PRIVATE_KEY)
    # web3.py v6 renamed .rawTransaction -> .raw_transaction; support both
    # so this keeps working whichever major version is installed.
    raw = getattr(signed, "raw_transaction", None) or getattr(signed, "rawTransaction", None)
    if raw is None:
        raise BlockchainAnchorError("Unexpected web3.py version: signed tx has no raw bytes attribute.")
    tx_hash = w3.eth.send_raw_transaction(raw)
    tx_hash_hex = tx_hash.hex()
    return tx_hash_hex if tx_hash_hex.startswith("0x") else f"0x{tx_hash_hex}"


def anchor_hash_to_blockchain(sha256_hex: str, *, wait_for_receipt: bool = False) -> str:
    """
    Anchors a SHA-256 file hash on-chain by calling HashAnchor.anchorHash().

    Args:
        sha256_hex: 64-char hex SHA-256 digest (with or without "0x").
        wait_for_receipt: if True, blocks until the transaction is mined
            (useful for a CLI/manual call); if False (the default, and what
            the upload endpoint uses), returns as soon as the transaction is
            broadcast so a slow block time never stalls the caller.

    Returns:
        The transaction hash as a "0x..." hex string.

    Raises:
        BlockchainAnchorError: anchoring is disabled/misconfigured, the
            node is unreachable, or the transaction was rejected.
        AlreadyAnchoredError: this exact hash is already on-chain.
    """
    if not settings.BLOCKCHAIN_PRIVATE_KEY:
        raise BlockchainAnchorError("BLOCKCHAIN_PRIVATE_KEY is not configured.")

    w3 = _get_web3()
    contract = _get_contract()
    file_hash = _hash_to_bytes32(sha256_hex)

    account = w3.eth.account.from_key(settings.BLOCKCHAIN_PRIVATE_KEY)

    # Read-only pre-check (free, no gas) -- avoids burning gas on a
    # transaction we already know the contract will revert.
    try:
        already = contract.functions.isAnchored(file_hash).call()
    except Exception as exc:  # noqa: BLE001
        raise BlockchainAnchorError(f"Could not reach contract at "
                                     f"{settings.BLOCKCHAIN_CONTRACT_ADDRESS}: {exc}") from exc
    if already:
        raise AlreadyAnchoredError(f"Hash {sha256_hex} is already anchored on-chain.")

    try:
        nonce = w3.eth.get_transaction_count(account.address, "pending")
        tx = contract.functions.anchorHash(file_hash).build_transaction(
            {
                "chainId": settings.BLOCKCHAIN_CHAIN_ID,
                "from": account.address,
                "nonce": nonce,
                "gas": settings.BLOCKCHAIN_GAS_LIMIT,
                "gasPrice": w3.eth.gas_price,
            }
        )
        tx_hash_hex = _sign_and_send(w3, tx)

        if wait_for_receipt:
            w3.eth.wait_for_transaction_receipt(
                tx_hash_hex, timeout=settings.BLOCKCHAIN_TX_TIMEOUT_SECONDS
            )
        return tx_hash_hex
    except BlockchainAnchorError:
        raise
    except Exception as exc:  # noqa: BLE001 - surface any web3/node error uniformly
        raise BlockchainAnchorError(f"Anchoring transaction failed: {exc}") from exc


def get_anchor_record(sha256_hex: str) -> AnchorRecord:
    """
    Free, read-only lookup of a hash's on-chain anchor record. Lets anyone
    (not just this API) independently verify anchoring without trusting our
    database's `blockchain_tx_hash` column.
    """
    contract = _get_contract()
    file_hash = _hash_to_bytes32(sha256_hex)
    try:
        anchored_by, timestamp = contract.functions.getRecord(file_hash).call()
    except Exception as exc:  # noqa: BLE001
        raise BlockchainAnchorError(f"Could not read anchor record: {exc}") from exc
    return AnchorRecord(anchored_by=anchored_by, timestamp=timestamp, exists=timestamp != 0)


def reset_connection_cache() -> None:
    """Drops the cached Web3 connection. Mainly useful for tests, or after
    changing BLOCKCHAIN_* settings at runtime."""
    _get_web3.cache_clear()
