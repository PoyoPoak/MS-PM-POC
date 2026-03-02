import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import EmailStr
from sqlalchemy import JSON, Column, DateTime, LargeBinary
from sqlmodel import Field, Relationship, SQLModel


def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime | None = None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime | None = None


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


class PacemakerTelemetryBase(SQLModel):
    patient_id: int = Field(index=True)
    timestamp: datetime = Field(
        sa_type=DateTime(timezone=True),  # type: ignore
        index=True,
    )
    lead_impedance_ohms: float
    capture_threshold_v: float
    r_wave_sensing_mv: float
    battery_voltage_v: float
    target_fail_next_7d: int | None = Field(default=None)
    lead_impedance_ohms_rolling_mean_3d: float | None = Field(default=None)
    lead_impedance_ohms_rolling_mean_7d: float | None = Field(default=None)
    capture_threshold_v_rolling_mean_3d: float | None = Field(default=None)
    capture_threshold_v_rolling_mean_7d: float | None = Field(default=None)
    lead_impedance_ohms_delta_per_day_3d: float | None = Field(default=None)
    lead_impedance_ohms_delta_per_day_7d: float | None = Field(default=None)
    capture_threshold_v_delta_per_day_3d: float | None = Field(default=None)
    capture_threshold_v_delta_per_day_7d: float | None = Field(default=None)


class PacemakerTelemetry(PacemakerTelemetryBase, table=True):
    __tablename__ = "pacemaker_telemetry"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class PacemakerTelemetryIngest(SQLModel):
    patient_id: int = Field(ge=0)
    timestamp: int = Field(
        ge=0,
        description="Unix epoch timestamp in seconds (UTC).",
    )
    lead_impedance_ohms: float
    capture_threshold_v: float
    r_wave_sensing_mv: float
    battery_voltage_v: float
    target_fail_next_7d: int | None = Field(default=None, ge=0, le=1)
    lead_impedance_ohms_rolling_mean_3d: float | None = Field(default=None)
    lead_impedance_ohms_rolling_mean_7d: float | None = Field(default=None)
    capture_threshold_v_rolling_mean_3d: float | None = Field(default=None)
    capture_threshold_v_rolling_mean_7d: float | None = Field(default=None)
    lead_impedance_ohms_delta_per_day_3d: float | None = Field(default=None)
    lead_impedance_ohms_delta_per_day_7d: float | None = Field(default=None)
    capture_threshold_v_delta_per_day_3d: float | None = Field(default=None)
    capture_threshold_v_delta_per_day_7d: float | None = Field(default=None)


class PacemakerTelemetryIngestResult(SQLModel):
    received_count: int
    inserted_count: int
    duplicate_count: int
    duplicate_in_payload_count: int
    duplicate_existing_count: int


class ModelArtifactUploadMetadata(SQLModel):
    client_version_id: str | None = Field(default=None, max_length=255)
    source_run_id: str | None = Field(default=None, max_length=255)
    trained_at_utc: datetime | None = None
    algorithm: str = Field(min_length=1, max_length=255)
    hyperparameters: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, Any]
    dataset_info: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = Field(default=None, max_length=2000)


class ModelArtifact(SQLModel, table=True):
    __tablename__ = "model_artifact"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    client_version_id: str | None = Field(default=None, max_length=255, index=True)
    source_run_id: str | None = Field(default=None, max_length=255, index=True)
    trained_at_utc: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    algorithm: str = Field(min_length=1, max_length=255)
    hyperparameters: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
    metrics: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
    dataset_info: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
    notes: str | None = Field(default=None, max_length=2000)
    content_type: str | None = Field(default=None, max_length=255)
    model_size_bytes: int
    model_sha256: str = Field(min_length=64, max_length=64, index=True)
    model_blob: bytes = Field(sa_column=Column(LargeBinary, nullable=False))


class ModelArtifactUploadResponse(SQLModel):
    id: uuid.UUID
    created_at: datetime | None = None
    client_version_id: str | None = None
    source_run_id: str | None = None
    algorithm: str
    model_size_bytes: int
    model_sha256: str
    content_type: str | None = None


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)
