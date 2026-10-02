from __future__ import annotations

from enum import StrEnum

from sqlalchemy import Column, Enum, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Grade(StrEnum):
    TK = "TK"
    K = "K"
    FIRST = "1st"
    SECOND = "2nd"
    THIRD = "3rd"
    FOURTH = "4th"
    FIFTH = "5th"
    SIXTH = "6th"
    SEVENTH = "7th"
    EIGHTH = "8th"


parent_members = Table(
    "parent_members",
    Base.metadata,
    Column("parent_id", ForeignKey("parents.id"), primary_key=True),
    Column("member_id", ForeignKey("members.id"), primary_key=True),
)


class Person(Base):
    __tablename__ = "people"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    person_type: Mapped[str] = mapped_column(String(50))

    __mapper_args__ = {
        "polymorphic_identity": "person",
        "polymorphic_on": person_type,
    }


class Parent(Person):
    __tablename__ = "parents"

    id: Mapped[int] = mapped_column(ForeignKey("people.id"), primary_key=True)
    primary_email: Mapped[str | None] = mapped_column(String(255))
    secondary_email: Mapped[str | None] = mapped_column(String(255))
    primary_phone: Mapped[str | None] = mapped_column(String(40))
    secondary_phone: Mapped[str | None] = mapped_column(String(40))

    members: Mapped[list[Member]] = relationship(
        secondary=parent_members,
        back_populates="parents",
    )

    __mapper_args__ = {"polymorphic_identity": "parent"}


class Member(Person):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(ForeignKey("people.id"), primary_key=True)
    age: Mapped[int | None]
    grade: Mapped[Grade | None] = mapped_column(
        Enum(
            Grade,
            values_callable=lambda grades: [grade.value for grade in grades],
            create_constraint=True,
        )
    )

    parents: Mapped[list[Parent]] = relationship(
        secondary=parent_members,
        back_populates="members",
    )

    __mapper_args__ = {"polymorphic_identity": "member"}
