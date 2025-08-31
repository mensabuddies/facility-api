from typing import List, Any
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel, Relationship, Column, create_engine, Session
from sqlalchemy.dialects.postgresql import JSONB

from app.src.config.env import db_username, db_password, db_url, db_name

connection_string = f'postgresql+psycopg2://{db_username}:{db_password}@{db_url}/{db_name}'

class Organization(SQLModel, table=True):
    __tablename__ = "organization"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True)
    domain: str = Field(max_length=100, unique=True)

    # relationships
    facilities: List["Facility"] = Relationship(back_populates="organization")

class Location(SQLModel, table=True):
    __tablename__ = "location"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True)

    # relationships
    facilities: List["Facility"] = Relationship(back_populates="location")

class FacilityType(SQLModel, table=True):
    __tablename__ = "facility_type"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True)

    # relationships
    facilities: List["Facility"] = Relationship(back_populates="facility_type")

class Facility(SQLModel, table=True):
    __tablename__ = "facility"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    address: str = Field(max_length=100)
    description: str = Field(max_length=250)
    uuid: str = Field(max_length=36, unique=True)

    # foreign keys
    organization_id: int = Field(foreign_key="organization.id", nullable=False)
    location_id: int = Field(foreign_key="location.id", nullable=False)
    facility_type_id: int = Field(foreign_key="facility_type.id", nullable=False)

    # relationships
    organization: Organization = Relationship(back_populates="facilities")
    location: Location = Relationship(back_populates="facilities")
    facility_type: FacilityType = Relationship(back_populates="facilities")

    notices: List["Notice"] = Relationship(
        back_populates="facility",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    opening_hours: List["OpeningHour"] = Relationship(
        back_populates="facility",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    meals: List["Meal"] = Relationship(
        back_populates="facility",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class Notice(SQLModel, table=True):
    __tablename__ = "notice"

    id: int | None = Field(default=None, primary_key=True)

    # foreign key
    facility_id: int = Field(foreign_key="facility.id", nullable=False)

    # when the notice was recorded (tz-aware)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # JSON array of notices (e.g., strings or objects)
    notices: dict[str, Any] = Field(
        sa_column=Column(JSONB)
    )

    # relationship back to Facility
    facility: Facility = Relationship(back_populates="notices")


class OpeningHour(SQLModel, table=True):
    __tablename__ = "opening_hours"

    id: int | None = Field(default=None, primary_key=True)

    # foreign key
    facility_id: int = Field(foreign_key="facility.id", nullable=False)

    # when the notice was recorded (tz-aware)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # JSON array of notices (e.g., strings or objects)
    opening_hours: dict[str, Any] = Field(
        sa_column=Column(JSONB)
    )

    # relationship back to Facility
    facility: Facility = Relationship(back_populates="opening_hours")


class Meal(SQLModel, table=True):
    __tablename__ = "meal"

    id: int | None = Field(default=None, primary_key=True)

    # foreign key
    facility_id: int = Field(foreign_key="facility.id", nullable=False)

    # when the notice was recorded (tz-aware)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # JSON array of notices (e.g., strings or objects)
    meals: dict[str, Any] = Field(
        sa_column=Column(JSONB)
    )

    # relationship back to Facility
    facility: Facility = Relationship(back_populates="meals")


engine = create_engine(connection_string, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session