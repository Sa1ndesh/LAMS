import enum


class UserRoleEnum(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    CENTRAL_MINISTRY = "CENTRAL_MINISTRY"
    STATE_AUTHORITY = "STATE_AUTHORITY"
    DISTRICT_ADMIN = "DISTRICT_ADMIN"
    LAND_ACQUISITION_OFFICER = "LAND_ACQUISITION_OFFICER"
    FIELD_OFFICER = "FIELD_OFFICER"
    PROJECT_IMPLEMENTING_AGENCY = "PROJECT_IMPLEMENTING_AGENCY"
    VIEWER = "VIEWER"


class ProjectCategoryEnum(str, enum.Enum):
    HIGHWAY = "Highway"
    RAILWAY = "Railway"
    METRO = "Metro"
    IRRIGATION = "Irrigation"
    INDUSTRIAL_CORRIDOR = "Industrial Corridor"
    RENEWABLE_ENERGY = "Renewable Energy"
    URBAN_DEVELOPMENT = "Urban Development"


class ProjectStageEnum(str, enum.Enum):
    PROPOSAL = "Proposal"
    VERIFICATION = "Verification"
    SURVEY = "Survey"
    NOTIFICATION = "Notification"
    AWARD = "Award"
    COMPENSATION = "Compensation"
    POSSESSION = "Possession"
    REHABILITATION = "Rehabilitation & Resettlement"
    COMPLETED = "Completed"


class ProjectStatusEnum(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ON_TRACK = "ON_TRACK"
    DELAYED = "DELAYED"
    CRITICAL = "CRITICAL"
    COMPLETED = "COMPLETED"
    ON_HOLD = "ON_HOLD"


class LandTypeEnum(str, enum.Enum):
    AGRICULTURAL = "Agricultural"
    COMMERCIAL = "Commercial"
    RESIDENTIAL = "Residential"
    FOREST = "Forest"
    GOVERNMENT = "Government"


class ParcelAcquisitionStatusEnum(str, enum.Enum):
    PROPOSED = "Proposed"
    VERIFIED = "Verified"
    SURVEYED = "Surveyed"
    NOTIFIED = "Notified"
    AWARDED = "Awarded"
    ACQUIRED = "Acquired"


class CompensationStatusEnum(str, enum.Enum):
    PENDING = "Pending"
    ASSESSED = "Assessed"
    APPROVED = "Approved"
    DISBURSED = "Disbursed"


class PossessionStatusEnum(str, enum.Enum):
    NOT_TAKEN = "Not Taken"
    DEMARCATED = "Demarcated"
    TAKEN = "Taken"


class PaymentStatusEnum(str, enum.Enum):
    ASSESSED = "ASSESSED"
    APPROVED = "APPROVED"
    PARTIALLY_DISBURSED = "PARTIALLY_DISBURSED"
    DISBURSED = "DISBURSED"
    PENDING = "PENDING"


class SocialCategoryEnum(str, enum.Enum):
    GENERAL = "GENERAL"
    OBC = "OBC"
    SC = "SC"
    ST = "ST"


class RRStatusEnum(str, enum.Enum):
    IDENTIFIED = "IDENTIFIED"
    ELIGIBLE = "ELIGIBLE"
    ASSISTANCE_DISBURSED = "ASSISTANCE_DISBURSED"
    RESETTLED = "RESETTLED"
    COMPLETED = "COMPLETED"


class MilestoneStatusEnum(str, enum.Enum):
    COMPLETED = "COMPLETED"
    IN_PROGRESS = "IN_PROGRESS"
    PENDING = "PENDING"
    DELAYED = "DELAYED"


class ApprovalStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class DocumentCategoryEnum(str, enum.Enum):
    PROPOSAL = "PROPOSAL"
    LAND_RECORDS = "LAND_RECORDS"
    SURVEY = "SURVEY"
    NOTIFICATIONS = "NOTIFICATIONS"
    AWARD = "AWARD"
    COMPENSATION = "COMPENSATION"
    RR = "RR"


class NotificationTypeEnum(str, enum.Enum):
    PROJECT_UPDATE = "PROJECT_UPDATE"
    STAGE_CHANGE = "STAGE_CHANGE"
    PARCEL_UPDATE = "PARCEL_UPDATE"
    COMPENSATION_UPDATE = "COMPENSATION_UPDATE"
    MILESTONE_DELAY = "MILESTONE_DELAY"
    DOCUMENT_UPDATE = "DOCUMENT_UPDATE"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"

