import sys
import os
# Ensure root backend path is in sys.path for standalone script execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, "/app")
sys.path.insert(0, os.getcwd())

import asyncio
import logging
import json
import uuid
from datetime import date, datetime, timezone
from sqlalchemy import select, text
from app.core.config import settings
from app.core.security import hash_password
from app.core.database import AsyncSessionLocal
from app.models import (
    Role,
    User,
    State,
    District,
    Project,
    LandOwner,
    Document,
    ProjectCategoryEnum,
    ProjectStageEnum,
    ProjectStatusEnum,
    LandTypeEnum,
    ParcelAcquisitionStatusEnum,
    CompensationStatusEnum,
    PossessionStatusEnum,
    DocumentCategoryEnum,
    UserRoleEnum,
    SocialCategoryEnum,
    RRStatusEnum,
    NotificationTypeEnum,
    PaymentStatusEnum,
    MilestoneStatusEnum,
)
from app.models.parcel import LandParcel
from app.models.compensation import CompensationRecord
from app.models.family import AffectedFamily, RehabilitationRecord
from app.models.project import Milestone, Approval
from app.models.notification import Notification
from app.models.audit import AuditLog

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("lams.seed")


async def seed_all():
    logger.info("Starting LAMS database seed sequence...")
    async with AsyncSessionLocal() as session:
        # Check if already seeded
        res = await session.execute(select(User).where(User.email == settings.SEED_ADMIN_EMAIL))
        if res.scalar_one_or_none():
            logger.info("Seed data already present in database. Skipping seed.")
            return

        # 1. Seed Roles
        logger.info("Seeding 8 LAMS administrative roles...")
        roles_data = [
            ("SUPER_ADMIN", "Full system administrator access"),
            ("CENTRAL_MINISTRY", "Central government ministry supervisor"),
            ("STATE_AUTHORITY", "State land acquisition authority officer"),
            ("DISTRICT_ADMIN", "District administration officer"),
            ("LAND_ACQUISITION_OFFICER", "Land acquisition officer (LAO)"),
            ("FIELD_OFFICER", "Field survey and verification officer"),
            ("PROJECT_IMPLEMENTING_AGENCY", "Project implementing agency representative"),
            ("VIEWER", "Read-only public and stakeholder viewer"),
        ]

        roles_dict = {}
        for role_name, role_desc in roles_data:
            role_obj = (await session.execute(select(Role).where(Role.name == role_name))).scalar_one_or_none()
            if not role_obj:
                role_obj = Role(name=role_name, description=role_desc)
                session.add(role_obj)
                await session.flush()
            roles_dict[role_name] = role_obj

        # 2. Seed Geography (States & Districts)
        logger.info("Seeding Indian states and key infrastructure districts...")
        states_data = [
            (1, "Maharashtra", "MH"),
            (2, "Gujarat", "GJ"),
            (3, "Uttar Pradesh", "UP"),
            (4, "Tamil Nadu", "TN"),
            (5, "Karnataka", "KA"),
        ]

        for s_id, s_name, s_code in states_data:
            st_obj = (await session.execute(select(State).where(State.id == s_id))).scalar_one_or_none()
            if not st_obj:
                session.add(State(id=s_id, name=s_name, code=s_code))

        districts_data = [
            (1, 1, "Thane", "THN"),
            (2, 1, "Raigad", "RGD"),
            (3, 2, "Surat", "SRT"),
            (4, 2, "Vadodara", "VDR"),
            (5, 3, "Gautam Buddha Nagar", "GBN"),
            (6, 4, "Kanchipuram", "KCP"),
            (7, 5, "Bengaluru Rural", "BLR"),
        ]

        for d_id, d_st_id, d_name, d_code in districts_data:
            dt_obj = (await session.execute(select(District).where(District.id == d_id))).scalar_one_or_none()
            if not dt_obj:
                session.add(District(id=d_id, state_id=d_st_id, name=d_name, code=d_code))

        await session.flush()

        # 3. Seed Users
        logger.info("Seeding default administrative users...")
        hashed_pwd = hash_password(settings.SEED_ADMIN_PASSWORD)
        admin_user = User(
            name="National Super Admin",
            email=settings.SEED_ADMIN_EMAIL,
            password_hash=hashed_pwd,
            role_id=roles_dict["SUPER_ADMIN"].id,
            state_id=None,
            district_id=None,
            is_active=True,
        )
        session.add(admin_user)

        sample_users = [
            ("Central Ministry Officer", "ministry.central@lams.gov.in", "CENTRAL_MINISTRY", None, None),
            ("Maharashtra State Authority", "state.mh@lams.gov.in", "STATE_AUTHORITY", 1, None),
            ("Gujarat State Authority", "state.gj@lams.gov.in", "STATE_AUTHORITY", 2, None),
            ("Thane District Admin", "district.thane@lams.gov.in", "DISTRICT_ADMIN", 1, 1),
            ("LAO Thane Project", "lao.thane@lams.gov.in", "LAND_ACQUISITION_OFFICER", 1, 1),
            ("Field Officer Vadodara", "field.vadodara@lams.gov.in", "FIELD_OFFICER", 2, 4),
            ("NHAI Implementing Agency", "agency.nhai@lams.gov.in", "PROJECT_IMPLEMENTING_AGENCY", None, None),
            ("Public Stakeholder Viewer", "viewer.public@lams.gov.in", "VIEWER", None, None),
        ]

        for u_name, u_email, u_role, u_st, u_dt in sample_users:
            u_obj = User(
                name=u_name,
                email=u_email,
                password_hash=hashed_pwd,
                role_id=roles_dict[u_role].id,
                state_id=u_st,
                district_id=u_dt,
                is_active=True,
            )
            session.add(u_obj)

        await session.flush()

        # 4. Seed Fictional Projects (5 Projects)
        logger.info("Seeding 5 fictional national infrastructure projects...")
        projects_seed = [
            {
                "project_code": "PROJ-MH-EXP-001",
                "name": "Mumbai-Nagpur Super Communication Expressway Phase II",
                "category": ProjectCategoryEnum.HIGHWAY,
                "description": "701 km access-controlled expressway corridor connecting Mumbai and Nagpur across 10 districts.",
                "ministry": "Ministry of Road Transport and Highways",
                "implementing_agency": "MSRDC",
                "state_id": 1,
                "district_id": 1,
                "village": "Wadhavan / Bhiwandi Junction",
                "land_proposed_hectares": 250.50,
                "land_acquired_hectares": 180.20,
                "budget_inr": 55000000000.0,
                "current_stage": ProjectStageEnum.COMPENSATION,
                "status": ProjectStatusEnum.ON_TRACK,
                "start_date": date(2025, 1, 15),
                "target_completion_date": date(2027, 12, 31),
            },
            {
                "project_code": "PROJ-GJ-DFCC-002",
                "name": "Western Dedicated Freight Corridor Rail Bypass",
                "category": ProjectCategoryEnum.RAILWAY,
                "description": "High-capacity electrified dual line freight rail corridor traversing Gujarat manufacturing belts.",
                "ministry": "Ministry of Railways",
                "implementing_agency": "DFCCIL",
                "state_id": 2,
                "district_id": 3,
                "village": "Hazira Industrial Belt",
                "land_proposed_hectares": 180.00,
                "land_acquired_hectares": 95.50,
                "budget_inr": 32000000000.0,
                "current_stage": ProjectStageEnum.SURVEY,
                "status": ProjectStatusEnum.DELAYED,
                "start_date": date(2025, 3, 1),
                "target_completion_date": date(2028, 6, 30),
            },
            {
                "project_code": "PROJ-UP-AIR-003",
                "name": "Noida International Greenfield Airport Expansion",
                "category": ProjectCategoryEnum.URBAN_DEVELOPMENT,
                "description": "Phase II land acquisition for runway 3 & 4 and cargo logistics terminal at Jewar.",
                "ministry": "Ministry of Civil Aviation",
                "implementing_agency": "YIAL / NIAL",
                "state_id": 3,
                "district_id": 5,
                "village": "Jewar / Dayanatpur",
                "land_proposed_hectares": 420.00,
                "land_acquired_hectares": 420.00,
                "budget_inr": 89000000000.0,
                "current_stage": ProjectStageEnum.COMPLETED,
                "status": ProjectStatusEnum.COMPLETED,
                "start_date": date(2024, 6, 1),
                "target_completion_date": date(2026, 5, 30),
            },
            {
                "project_code": "PROJ-TN-PORT-004",
                "name": "Ennore Deep Ocean Port Container Terminal",
                "category": ProjectCategoryEnum.INDUSTRIAL_CORRIDOR,
                "description": "Coastal acquisition for deep-draft container berth extension and rail transshipment yard.",
                "ministry": "Ministry of Ports, Shipping and Waterways",
                "implementing_agency": "Kamarajar Port Limited",
                "state_id": 4,
                "district_id": 6,
                "village": "Kattupalli Coastal Belt",
                "land_proposed_hectares": 110.00,
                "land_acquired_hectares": 30.00,
                "budget_inr": 18000000000.0,
                "current_stage": ProjectStageEnum.NOTIFICATION,
                "status": ProjectStatusEnum.CRITICAL,
                "start_date": date(2025, 5, 10),
                "target_completion_date": date(2027, 9, 30),
            },
            {
                "project_code": "PROJ-KA-ENRG-005",
                "name": "Pavagada Solar Park Transmission Grid Infrastructure",
                "category": ProjectCategoryEnum.RENEWABLE_ENERGY,
                "description": "Green energy corridor grid sub-station expansion and ultra-high voltage power line right-of-way.",
                "ministry": "Ministry of New and Renewable Energy",
                "implementing_agency": "KSPDCL",
                "state_id": 5,
                "district_id": 7,
                "village": "Pavagada Solar Zone",
                "land_proposed_hectares": 310.00,
                "land_acquired_hectares": 290.00,
                "budget_inr": 24000000000.0,
                "current_stage": ProjectStageEnum.POSSESSION,
                "status": ProjectStatusEnum.ON_TRACK,
                "start_date": date(2024, 11, 15),
                "target_completion_date": date(2026, 11, 30),
            },
        ]

        created_projects = []
        for p_data in projects_seed:
            proj = Project(**p_data)
            session.add(proj)
            created_projects.append(proj)

        await session.flush()

        # 5. Seed 25 Land Parcels with PostGIS Geometries (SRID 4326)
        logger.info("Seeding 25 land parcels with closed Polygon geometries (SRID 4326)...")
        # Geometries for each project location
        coords_presets = [
            # Mumbai Corridor (Thane/Raigad)
            [
                [(73.01, 19.20), (73.03, 19.20), (73.03, 19.22), (73.01, 19.22), (73.01, 19.20)],
                [(73.04, 19.21), (73.06, 19.21), (73.06, 19.23), (73.04, 19.23), (73.04, 19.21)],
                [(73.07, 19.22), (73.09, 19.22), (73.09, 19.24), (73.07, 19.24), (73.07, 19.22)],
                [(73.10, 19.23), (73.12, 19.23), (73.12, 19.25), (73.10, 19.25), (73.10, 19.23)],
                [(73.13, 19.24), (73.15, 19.24), (73.15, 19.26), (73.13, 19.26), (73.13, 19.24)],
            ],
            # Gujarat Freight Corridor
            [
                [(72.82, 21.15), (72.84, 21.15), (72.84, 21.17), (72.82, 21.17), (72.82, 21.15)],
                [(72.85, 21.16), (72.87, 21.16), (72.87, 21.18), (72.85, 21.18), (72.85, 21.16)],
                [(72.88, 21.17), (72.90, 21.17), (72.90, 21.19), (72.88, 21.19), (72.88, 21.17)],
                [(72.91, 21.18), (72.93, 21.18), (72.93, 21.20), (72.91, 21.20), (72.91, 21.18)],
                [(72.94, 21.19), (72.96, 21.19), (72.96, 21.21), (72.94, 21.21), (72.94, 21.19)],
            ],
            # Noida Airport
            [
                [(77.53, 28.14), (77.55, 28.14), (77.55, 28.16), (77.53, 28.16), (77.53, 28.14)],
                [(77.56, 28.15), (77.58, 28.15), (77.58, 28.17), (77.56, 28.17), (77.56, 28.15)],
                [(77.59, 28.16), (77.61, 28.16), (77.61, 28.18), (77.59, 28.18), (77.59, 28.16)],
                [(77.62, 28.17), (77.64, 28.17), (77.64, 28.19), (77.62, 28.19), (77.62, 28.17)],
                [(77.65, 28.18), (77.67, 28.18), (77.67, 28.20), (77.65, 28.20), (77.65, 28.18)],
            ],
            # Ennore Port
            [
                [(80.30, 13.25), (80.32, 13.25), (80.32, 13.27), (80.30, 13.27), (80.30, 13.25)],
                [(80.33, 13.26), (80.35, 13.26), (80.35, 13.28), (80.33, 13.28), (80.33, 13.26)],
                [(80.36, 13.27), (80.38, 13.27), (80.38, 13.29), (80.36, 13.29), (80.36, 13.27)],
                [(80.39, 13.28), (80.41, 13.28), (80.41, 13.30), (80.39, 13.30), (80.39, 13.28)],
                [(80.42, 13.29), (80.44, 13.29), (80.44, 13.31), (80.42, 13.31), (80.42, 13.29)],
            ],
            # Pavagada Solar Park
            [
                [(77.25, 14.08), (77.27, 14.08), (77.27, 14.10), (77.25, 14.10), (77.25, 14.08)],
                [(77.28, 14.09), (77.30, 14.09), (77.30, 14.11), (77.28, 14.11), (77.28, 14.09)],
                [(77.31, 14.10), (77.33, 14.10), (77.33, 14.12), (77.31, 14.12), (77.31, 14.10)],
                [(77.34, 14.11), (77.36, 14.11), (77.36, 14.13), (77.34, 14.13), (77.34, 14.11)],
                [(77.37, 14.12), (77.39, 14.12), (77.39, 14.14), (77.37, 14.14), (77.37, 14.12)],
            ],
        ]

        land_types = [
            LandTypeEnum.AGRICULTURAL,
            LandTypeEnum.COMMERCIAL,
            LandTypeEnum.RESIDENTIAL,
            LandTypeEnum.FOREST,
            LandTypeEnum.GOVERNMENT,
        ]
        acq_statuses = [
            ParcelAcquisitionStatusEnum.ACQUIRED,
            ParcelAcquisitionStatusEnum.SURVEYED,
            ParcelAcquisitionStatusEnum.PROPOSED,
            ParcelAcquisitionStatusEnum.NOTIFIED,
        ]
        comp_statuses = [
            CompensationStatusEnum.DISBURSED,
            CompensationStatusEnum.APPROVED,
            CompensationStatusEnum.APPROVED,
            CompensationStatusEnum.ASSESSED,
            CompensationStatusEnum.PENDING,
        ]
        poss_statuses = [
            PossessionStatusEnum.TAKEN,
            PossessionStatusEnum.DEMARCATED,
            PossessionStatusEnum.NOT_TAKEN,
        ]

        parcel_count = 0
        for p_idx, project in enumerate(created_projects):
            presets = coords_presets[p_idx]
            for i in range(5):
                parcel_count += 1
                poly_pts = presets[i]
                wkt_poly = f"POLYGON(({','.join(f'{lon} {lat}' for lon, lat in poly_pts)}))"

                center_lat = poly_pts[0][1] + 0.01
                center_lon = poly_pts[0][0] + 0.01

                land_type = land_types[i % len(land_types)]
                acq_status = acq_statuses[(p_idx + i) % len(acq_statuses)]
                comp_status = comp_statuses[(p_idx + i) % len(comp_statuses)]
                poss_status = poss_statuses[(p_idx + i) % len(poss_statuses)]

                pcl_code = f"PCL-{project.project_code[-3:]}-{i+1:03d}"
                survey_num = f"SY-{100 + parcel_count}/{i+1}"

                parcel = LandParcel(
                    project_id=project.id,
                    parcel_code=pcl_code,
                    survey_number=survey_num,
                    state_id=project.state_id,
                    district_id=project.district_id,
                    taluk=f"Taluk-{project.district_id}",
                    village=project.village,
                    area_hectares=round(10.0 + (i * 3.5), 2),
                    land_type=land_type,
                    acquisition_status=acq_status,
                    compensation_status=comp_status,
                    possession_status=poss_status,
                    latitude=center_lat,
                    longitude=center_lon,
                    geometry=wkt_poly,
                )
                session.add(parcel)
                await session.flush()

                # Seed Land Owner
                owner = LandOwner(
                    parcel_id=parcel.id,
                    owner_reference=f"OWN-{parcel_count:04d}",
                    display_name=f"Farmer {parcel_count} & Family",
                )
                session.add(owner)

                # Seed Compensation Record
                pay_status = PaymentStatusEnum.DISBURSED if (p_idx + i) % 3 == 0 else PaymentStatusEnum.APPROVED
                comp = CompensationRecord(
                    project_id=project.id,
                    parcel_id=parcel.id,
                    assessed_amount_inr=15000000.0 + (i * 2000000.0),
                    approved_amount_inr=15000000.0 + (i * 2000000.0),
                    disbursed_amount_inr=15000000.0 + (i * 2000000.0) if pay_status == PaymentStatusEnum.DISBURSED else 5000000.0,
                    payment_status=pay_status,
                    payment_date=date(2025, 8, 15),
                )
                session.add(comp)

                # Seed Affected Family
                fam = AffectedFamily(
                    project_id=project.id,
                    family_reference_id=f"FAM-{parcel_count:04d}",
                    village=project.village,
                    category=SocialCategoryEnum.OBC if i % 2 == 0 else SocialCategoryEnum.SC,
                    is_affected=True,
                    is_displaced=True if i % 3 == 0 else False,
                    rr_status=RRStatusEnum.COMPLETED if acq_status == ParcelAcquisitionStatusEnum.ACQUIRED else RRStatusEnum.IDENTIFIED,
                )
                session.add(fam)

        # 6. Seed Milestones & Notifications
        logger.info("Seeding project milestones and initial notifications...")
        for project in created_projects:
            m1 = Milestone(
                project_id=project.id,
                title="Section 4 Notification Issued",
                stage="Notification",
                planned_date=date(2025, 2, 1),
                actual_date=date(2025, 2, 5),
                status=MilestoneStatusEnum.COMPLETED,
            )
            m2 = Milestone(
                project_id=project.id,
                title="Section 11 Preliminary Survey Published",
                stage="Survey",
                planned_date=date(2025, 6, 15),
                actual_date=date(2025, 6, 20),
                status=MilestoneStatusEnum.COMPLETED,
            )
            m3 = Milestone(
                project_id=project.id,
                title="Section 19 Compensation Award Declaration",
                stage="Award",
                planned_date=date(2026, 1, 10),
                status=MilestoneStatusEnum.IN_PROGRESS if project.status != ProjectStatusEnum.COMPLETED else MilestoneStatusEnum.COMPLETED,
            )
            session.add_all([m1, m2, m3])

            notif = Notification(
                user_id=admin_user.id,
                project_id=project.id,
                title=f"Project Setup Completed: {project.name}",
                message=f"Project {project.project_code} initialized at stage {project.current_stage.value}.",
                notification_type=NotificationTypeEnum.PROJECT_UPDATE,
                is_read=False,
            )
            session.add(notif)

            audit = AuditLog(
                user_id=admin_user.id,
                action="PROJECT_CREATED",
                entity_type="PROJECT",
                entity_id=str(project.id),
                new_value={"project_code": project.project_code, "name": project.name},
            )
            session.add(audit)

        await session.commit()
        logger.info("✅ LAMS database successfully seeded with all initial data, PostGIS geometries, and users!")


if __name__ == "__main__":
    asyncio.run(seed_all())
