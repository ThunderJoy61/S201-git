from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Region(Base):
    __tablename__ = "region"

    id = Column(Integer, primary_key=True)
    code = Column(String(10), nullable=False)
    libelle = Column(String(100), nullable=False)

    departements = relationship("Departement", back_populates="region")

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "libelle": self.libelle
        }


class Departement(Base):
    __tablename__ = "departement"

    id = Column(Integer, primary_key=True)
    code = Column(String(10), nullable=False)
    libelle = Column(String(100), nullable=False)
    region_id = Column(Integer, ForeignKey("region.id"), nullable=False)

    region = relationship("Region", back_populates="departements")

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "libelle": self.libelle,
            "region_id": self.region_id
        }


class ProfessionSante(Base):
    __tablename__ = "profession_sante"

    id = Column(Integer, primary_key=True)
    libelle = Column(String(200), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "libelle": self.libelle
        }


class Sexe(Base):
    __tablename__ = "sexe"

    id = Column(Integer, primary_key=True)
    libelle = Column(String(50), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "libelle": self.libelle
        }


class TrancheAge(Base):
    __tablename__ = "tranche_age"

    id = Column(Integer, primary_key=True)
    libelle = Column(String(100), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "libelle": self.libelle
        }


class TypeExercice(Base):
    __tablename__ = "type_exercice"

    id = Column(Integer, primary_key=True)
    libelle = Column(String(200), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "libelle": self.libelle
        }


class TypeHonoraire(Base):
    __tablename__ = "type_honoraire"

    id = Column(Integer, primary_key=True)
    niveau_1 = Column(String(80), nullable=False)
    niveau_2 = Column(String(80), nullable=True)
    niveau_3 = Column(String(80), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "niveau_1": self.niveau_1,
            "niveau_2": self.niveau_2,
            "niveau_3": self.niveau_3
        }


class TypePrescription(Base):
    __tablename__ = "type_prescription"

    id = Column(Integer, primary_key=True)
    libelle = Column(String(200), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "libelle": self.libelle
        }


class TypeSecteur(Base):
    __tablename__ = "type_secteur"

    id = Column(Integer, primary_key=True)
    code = Column(String(20), nullable=False)
    libelle = Column(String(200), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "libelle": self.libelle
        }