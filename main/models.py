from datetime import datetime
from enum import Enum

from flask_login import UserMixin
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import backref

from main import db, login


@login.user_loader
def load_user(person_id):
    return Person.query.get(int(person_id))


class GenderType(Enum):
    Male = 'Male'
    Female = 'Female'


class PersonType(Enum):
    Expert = 'Expert'
    Assistant = 'Assistant'
    DeptProf = 'DeptProf'
    OtherProf = 'OtherProf'
    Student = 'Student'


class MeetingType(Enum):
    # 系務會議
    DeptAffairs = 'DeptAffairs'
    # 系教評會
    FacultyEvaluation = 'FacultyEvaluation'
    # 系課程委員會
    DeptCurriculum = 'DeptCurriculum'
    # 招生暨學生事務委員會
    StudentAffairs = 'StudentAffairs'
    # 系發展協會
    DeptDevelopment = 'DeptDevelopment'
    # 其他
    Other = 'Other'


class StudentProgramType(Enum):
    UnderGraduate = 'UnderGraduate'
    Graduate = 'Graduate'
    PhD = 'PhD'


class StudentStudyYearType(Enum):
    FirstYear = 'FirstYear'
    SecondYear = 'SecondYear'
    ThirdYear = 'ThirdYear'
    ForthYear = 'ForthYear'
    FifthYear = 'FifthYear'
    SixthYear = 'SixthYear'
    SeventhYear = 'SeventhYear'


class MotionStatusType(Enum):
    InDiscussion = 'InDiscussion'
    InExecution = 'InExecution'
    Closed = 'Closed'


class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    type = db.Column(db.Enum(MeetingType), nullable=False)
    time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    location = db.Column(db.String(50), nullable=False)
    is_draft = db.Column(db.Boolean, nullable=False, default=True)

    attachments = db.relationship('Attachment', backref='meeting', cascade='all, delete-orphan')
    announcements = db.relationship('Announcement', backref='meeting', cascade='all, delete-orphan')
    extempores = db.relationship('Extempore', backref='meeting', cascade='all, delete-orphan')
    motions = db.relationship('Motion', backref='meeting', cascade='all, delete-orphan')

    chair_id = db.Column(db.Integer, db.ForeignKey('person.id'))
    chair_speech = db.Column(db.Text)
    chair_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    chair = db.relationship('Person', foreign_keys=[chair_id], uselist=False, backref='meetings_as_chair')

    minute_taker_id = db.Column(db.Integer, db.ForeignKey('person.id'))
    minute_taker = db.relationship('Person', foreign_keys=[minute_taker_id], uselist=False,
                                   backref='meetings_as_minute_taker')

    attendees = association_proxy('attendee_association', 'attendee',
                                  creator=lambda attendee: Attendee(attendee=attendee))

    def __repr__(self):
        return f'<Meeting {self.id} {self.title} {self.type.value}>'

    def attendees_filter_by(self, **kwargs):
        return Person.query.filter_by(**kwargs).join(Attendee).join(Meeting).filter_by(id=self.id)


class Person(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.Enum(GenderType), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False, unique=True)
    type = db.Column(db.Enum(PersonType), nullable=False)

    expert_info = db.relationship('Expert', backref='basic_info', uselist=False, cascade='all, delete-orphan')
    assistant_info = db.relationship('Assistant', backref='basic_info', uselist=False, cascade='all, delete-orphan')
    dept_prof_info = db.relationship('DeptProf', backref='basic_info', uselist=False, cascade='all, delete-orphan')
    other_prof_info = db.relationship('OtherProf', backref='basic_info', uselist=False, cascade='all, delete-orphan')
    student_info = db.relationship('Student', backref='basic_info', uselist=False, cascade='all, delete-orphan')

    meetings_as_attendee = association_proxy('attendee_association', 'meeting',
                                             creator=lambda meeting: Attendee(meeting=meeting))

    def add_expert(self, company_name, job_title, office_tel, address, bank_account):
        expert = Expert()
        expert.company_name = company_name
        expert.job_title = job_title
        expert.office_tel = office_tel
        expert.address = address
        expert.bank_account = bank_account
        self.expert_info = expert

    def add_assistant(self, office_tel):
        assistant = Assistant()
        assistant.office_tel = office_tel
        self.assistant_info = assistant

    def add_dept_prof(self, job_title, office_tel):
        dept_prof = DeptProf()
        dept_prof.job_title = job_title
        dept_prof.office_tel = office_tel
        self.dept_prof_info = dept_prof

    def add_other_prof(self, univ_name, dept_name, job_title, office_tel, address, bank_account):
        other_prof = OtherProf()
        other_prof.univ_name = univ_name
        other_prof.dept_name = dept_name
        other_prof.job_title = job_title
        other_prof.office_tel = office_tel
        other_prof.address = address
        other_prof.bank_account = bank_account
        self.other_prof_info = other_prof

    def add_student(self, student_id, program, study_year):
        student = Student()
        student.student_id = student_id
        student.program = program
        student.study_year = study_year
        self.student_info = student

    def __repr__(self):
        return f'<Person {self.id} {self.name} {self.type.value}>'


class Attendee(db.Model):
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'), primary_key=True)
    meeting = db.relationship(Meeting, backref=backref('attendee_association', cascade='all, delete-orphan'))
    attendee = db.relationship(Person, backref=backref('attendee_association', cascade='all, delete-orphan'))
    is_present = db.Column(db.Boolean, nullable=False, default=False)
    is_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    is_member = db.Column(db.Boolean, nullable=False, default=True)

    def __repr__(self):
        return f'<Attendee {self.meeting.title} {self.attendee.name}>'


class Expert(db.Model):
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'), primary_key=True)
    company_name = db.Column(db.String(50), nullable=False)
    job_title = db.Column(db.String(50), nullable=False)
    office_tel = db.Column(db.String(20))
    address = db.Column(db.String(500))
    bank_account = db.Column(db.String(50))


class Assistant(db.Model):
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'), primary_key=True)
    office_tel = db.Column(db.String(20))


class DeptProf(db.Model):
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'), primary_key=True)
    job_title = db.Column(db.String(50), nullable=False)
    office_tel = db.Column(db.String(20))


class OtherProf(db.Model):
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'), primary_key=True)
    univ_name = db.Column(db.String(50), nullable=False)
    dept_name = db.Column(db.String(50), nullable=False)
    job_title = db.Column(db.String(50), nullable=False)
    office_tel = db.Column(db.String(20))
    address = db.Column(db.String(500))
    bank_account = db.Column(db.String(50))


class Student(db.Model):
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'), primary_key=True)
    student_id = db.Column(db.String(50), nullable=False, unique=True)
    program = db.Column(db.Enum(StudentProgramType), nullable=False)
    study_year = db.Column(db.Enum(StudentStudyYearType), nullable=False)


class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(100), nullable=False)


class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), primary_key=True)
    content = db.Column(db.Text, nullable=False)


class Extempore(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), primary_key=True)
    content = db.Column(db.Text, nullable=False)


class Motion(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), primary_key=True)
    description = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text)
    status = db.Column(db.Enum(MotionStatusType), nullable=False, default=MotionStatusType.InDiscussion)
    resolution = db.Column(db.Text)
    execution = db.Column(db.Text)
