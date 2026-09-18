from app.database import Base, SessionLocal, engine
from app.models import Case, CaseStatus, User, UserRole, UserStatus
from app.security import hash_password

Base.metadata.create_all(bind=engine)

DEMO_PASSWORD = "NyayVault@123"  # same password for every seeded demo account

DEMO_USERS = [
    dict(full_name="Insp. R. Sharma", username="officer.sharma", badge_id="IO-2291",
         role=UserRole.io, status=UserStatus.approved),
    dict(full_name="Dr. A. Rao", username="dr.rao", badge_id="FS-1042",
         role=UserRole.forensic, status=UserStatus.approved),
    dict(full_name="Justice K. Verma", username="justice.verma", badge_id="JC-0087",
         role=UserRole.judge, status=UserStatus.approved),
    dict(full_name="Insp. M. Bhatt", username="officer.bhatt", badge_id="IO-2340",
         role=UserRole.io, status=UserStatus.pending),
    dict(full_name="System Administrator", username="admin", badge_id="AD-0001",
         role=UserRole.admin, status=UserStatus.approved),
]

DEMO_CASES = [
    dict(number="FIR-2026-0341", title="State vs. Rakesh Malhotra", status=CaseStatus.active),
    dict(number="FIR-2026-0298", title="State vs. Unknown (Cyber Fraud)", status=CaseStatus.court),
    dict(number="FIR-2026-0187", title="State vs. Devendra Rawat", status=CaseStatus.closed),
    dict(number="FIR-2026-0355", title="State vs. Priya Nair", status=CaseStatus.active),
]


def run():
    db = SessionLocal()
    try:
        created_users = {}
        for u in DEMO_USERS:
            existing = db.query(User).filter(User.username == u["username"]).first()
            if existing:
                created_users[u["username"]] = existing
                continue
            user = User(**u, hashed_password=hash_password(DEMO_PASSWORD))
            db.add(user)
            db.flush()
            created_users[u["username"]] = user

        io_user = created_users["officer.sharma"]

        for c in DEMO_CASES:
            existing = db.query(Case).filter(Case.number == c["number"]).first()
            if existing:
                continue
            db.add(Case(**c, created_by_id=io_user.id))

        db.commit()
        print("Seed complete.")
        print(f"Demo password for every account: {DEMO_PASSWORD}")
        for u in DEMO_USERS:
            print(f"  - {u['username']:<16} role={u['role'].value:<9} badge={u['badge_id']}  status={u['status'].value}")
        print("\nEvidence documents are not seeded with placeholder files -- ")
        print("upload real files through the 'io' or 'forensic' accounts to")
        print("populate a case with real, hashed evidence.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
