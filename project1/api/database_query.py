from sqlite3 import Connection
from typing import List, Union

from fastapi import HTTPException, status, Depends
from loguru import logger
from typing import Optional


from .models import (
    AvailableClass,
    EnrollmentRequest,
    EnrollmentResponse,
    QueryStatus,
    Registration,
    RegistrationStatus,
    UserRole,
    EnrollmentListResponse,
    WaitlistStudents,
    WaitlistPositionList,
    DropStudentRequest
)

LIST_AVAILABLE_SQL_QUERY = """
	SELECT available_classes.name as 'course_name', available_classes.coursecode as 'course_code', 
    available_classes.department, available_classes.currentenrollment as 'current_enrollment', 
    available_classes.waitlist, available_classes.maxenrollment as "max_enrollment", 
    available_classes.sectionnumber as "section_number", 
    ur.name as "instructor_first_name", ur.lastname as "instructor_last_name"  
    FROM Users ur, (SELECT cl.coursecode, cl.name, cl.department, sc.currentenrollment, 
    sc.maxenrollment, sc.waitlist, sc.sectionnumber, sc.instructorid FROM "Class" as cl 
    join section as sc on cl.coursecode = sc.coursecode WHERE cl.Department = '{department_name}') 
    as available_classes where ur.cwid = available_classes.instructorid
"""
WAITLIST_ALLOWED = 15
class DBException(Exception):
    def __init__(self, error_detail:str) -> None:
        self.error_detail = error_detail


    
def get_available_classes(db_connection: Connection, department_name: str) -> List[AvailableClass]:
    """Query database to get available classes for a given department name

    Args:
        db_connection (Connection): SQLite Connection 
        department_name (str): Department name

    Returns:
        List[AvailableClass]: List of available classes
    """
    result = []
    query = LIST_AVAILABLE_SQL_QUERY.format(department_name=department_name)
    cursor = db_connection.cursor()
    rows =  cursor.execute(query)
    if rows.arraysize == 0:
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail= f'Record not found for given department_name:{department_name}')
    for row in rows:
        available_class = AvailableClass(course_name=row[0], 
                                     course_code=row[1],
                                     department=row[2],
                                     current_enrollment=row[3],
                                     waitlist=row[4],
                                     max_enrollment=row[5],
                                     section_number=row[6],
                                     instructor_first_name=row[7],
                                     instructor_last_name=row[8])
        result.append(available_class)
    cursor.close()
    return result


def check_user_role(db_connection: Connection, student_id: int)-> Union[str, None]:
    logger.info('Checking user role')
    query = f"""
            SELECT role FROM Users where CWID = {student_id} 
            """
    cursor = db_connection.cursor()
    rows =  cursor.execute(query)
    if rows.arraysize == 0:
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail= f'Record not found for given student_id:{student_id}')
    result = UserRole.NOT_FOUND
    for row in rows:
        result = row[0]
    return result


def count_waitlist_registration(db_connection: Connection, section_id: int)->int:
    logger.info('Checking waitlist registration')
    query = f"""SELECT COUNT(*) FROM RegistrationList WHERE ClassID = {section_id} and Status = 'waitlisted'
    """
    cursor = db_connection.cursor()
    rows =  cursor.execute(query)
    if rows.arraysize == 0:
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail= f'Record not found for given section_id:{section_id}')
    result = 0
    for row in rows:
        result = row[0]
    return result

def check_enrollment_eligibility(db_connection: Connection, section_number: int, course_code: str)->str:
    logger.info('Checking enrollment eligibility')
    query = f"""SELECT CurrentEnrollment as 'current_enrollment', MaxEnrollment as 'max_enrollment', Waitlist as 'waitlist' FROM "Section" WHERE CourseCode = '{course_code}' and SectionNumber = {section_number}
    """

    cursor = db_connection.cursor()
    rows =  cursor.execute(query)
    if rows.arraysize == 0:
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail= f'Record not found for given section_number:{section_number} and course_code:{course_code}')
    query_result = {}
    for row in rows:
        query_result['current_enrollment'] = row[0]
        query_result['max_enrollment'] = row[1]
        query_result['waitlist'] = row[2]
    
    # First check whether there is capacity to enroll in a section
    if query_result['max_enrollment'] - query_result['current_enrollment'] >= 1:
        return RegistrationStatus.ENROLLED
    
    if query_result['waitlist'] <= WAITLIST_ALLOWED:
        return RegistrationStatus.WAITLISTED
    
    return RegistrationStatus.NOT_ELIGIBLE

def check_status_query(db_connection: Connection, enrollment_request: EnrollmentRequest) -> Union[EnrollmentResponse, None]:
    check_status_query = f""" SELECT Status, EnrollmentDate FROM RegistrationList where StudentID = {enrollment_request.student_id} and SectionNumber = {enrollment_request.section_number} and CourseCode = '{enrollment_request.course_code}'"""
    cursor = db_connection.cursor()
    try:
        rows =  cursor.execute(check_status_query)
        if rows.arraysize == 0:
            raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail= f'Record not found')
        for row in rows:
            if row[0] == RegistrationStatus.ENROLLED:
                return EnrollmentResponse(enrollment_status="already enrolled", enrollment_date=row[1])
    except Exception as err:
        logger.error(err)
        raise DBException(error_detail = 'Fail to register')
    return None


def complete_registration(db_connection: Connection, registration: Registration) -> str:
    logger.info('Starting registration')
    insert_query = f"""
    INSERT INTO RegistrationList (StudentID,CourseCode, SectionNumber, Status) VALUES ({registration.student_id},'{registration.course_code}', {registration.section_number}, '{registration.enrollment_status}')
    """
    update_current_enrollment_query = f"""
    UPDATE "Section" SET CurrentEnrollment = CurrentEnrollment + 1 WHERE SectionNumber = {registration.section_number} and CourseCode = '{registration.course_code}'
    """
    update_waitlist_query = f"""
    UPDATE "Section" SET Waitlist = Waitlist + 1 WHERE SectionNumber = {registration.section_number} and CourseCode = '{registration.course_code}'
    """

    cursor = db_connection.cursor()
    cursor.execute("BEGIN")
    try:
        cursor.execute(insert_query)
        if registration.enrollment_status == RegistrationStatus.ENROLLED:
            cursor.execute(update_current_enrollment_query)
        elif registration.enrollment_status == RegistrationStatus.WAITLISTED:
            cursor.execute(update_waitlist_query)
        cursor.execute("COMMIT")
    except Exception as err:
        logger.error(err)
        cursor.execute("ROLLBACK")
        logger.info('Rolling back transaction')
        raise DBException(error_detail = 'Fail to register')
    finally:
        cursor.close()

    return QueryStatus.SUCCESS

def update_student_registration_status(db_connection:Connection, registration: Registration)-> str:
    logger.info('Upadting the registration status')
    check_status_query = f""" SELECT Status FROM RegistrationList where StudentID = {registration.student_id} and SectionNumber = {registration.section_number} and CourseCode = '{registration.course_code}'"""
    update_status_query = f""" UPDATE RegistrationList SET Status = 'dropped' where StudentID = {registration.student_id} and 
                               SectionNumber = {registration.section_number} and CourseCode = '{registration.course_code}' and status = 'enrolled' """
    update_current_enrollment_query = f"""UPDATE SECTION set CurrentEnrollment = CurrentEnrollment -1 where SectionNumber = {registration.section_number} and CourseCode = '{registration.course_code}'"""
    update_waitlist_count_query = f"""UPDATE "Section" SET Waitlist = Waitlist - 1 WHERE SectionNumber = {registration.section_number} and CourseCode = '{registration.course_code}'"""
    cursor = db_connection.cursor()
    cursor.execute("BEGIN")
    try:
        rows =  cursor.execute(check_status_query)
        if rows.arraysize == 0:
            raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail= f'Record not found')
        row = rows.fetchone()
        if row[0] == RegistrationStatus.DROPPED:
            return RegistrationStatus.DROPPED
        else:
            cursor.execute(update_status_query)
            if row[0] == RegistrationStatus.ENROLLED:
                cursor.execute(update_current_enrollment_query)
            elif row[0] == RegistrationStatus.WAITLISTED:
                cursor.execute(update_waitlist_count_query)
        cursor.execute("COMMIT")
    except Exception as err:
        logger.error(err)
        cursor.execute("ROLLBACK")
        logger.info('Rolling back transaction')
        raise DBException(error_detail = 'Fail to drop the class')
    finally:
        cursor.close()
    return QueryStatus.SUCCESS
        
    
def check_class_exists(db_connection: Connection, course_code: str)-> bool:
    logger.info('Checking if class exists')
    result = False
    query = f"""
            SELECT CourseCode FROM Class where CourseCode = '{course_code}' 
            """
    cursor = db_connection.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    if len(rows) > 0:
        result = True
    return result


def check_section_exists(db_connection: Connection, course_code: str, section_number: int)-> bool:
    logger.info('Checking if section exists')
    result = False
    query = f"""
            SELECT SectionNumber FROM Section where CourseCode = '{course_code}' and SectionNumber = {section_number}
            """
    cursor = db_connection.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    if len(rows) > 0:
        result = True
    return result


def check_is_instructor(db_connection: Connection, instructor_id: int)-> Union[str, None]:
    logger.info('Checking if user is instructor')
    query = f"""
            SELECT role FROM Users where CWID = {instructor_id}
            """
    cursor = db_connection.cursor()
    rows =  cursor.execute(query)
    if rows.arraysize == 0:
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail= f'Record not found for given CWID: {instructor_id}')
    result = UserRole.NOT_FOUND
    for row in rows:
        result = row[0]
    return result


def addClass(db_connection: Connection, course_code, class_name, department) -> str:
    logger.info('Starting to add class')
    insert_query = f"""
    INSERT INTO Class (CourseCode, Name, Department) VALUES ('{course_code}', '{class_name}', '{department}')
    """

    cursor = db_connection.cursor()

    cursor.execute("BEGIN")
    try:
        cursor.execute(insert_query)
        cursor.execute("COMMIT")
    except Exception as err:
        logger.error(err)
        cursor.execute("ROLLBACK")
        logger.info('Rolling back transaction')
        raise DBException(error_detail = 'Fail to add class')
    finally:
        cursor.close()

    return QueryStatus.SUCCESS

def addSection(db_connection: Connection, section_number, course_code, instructor_id, max_enrollment) -> str:
    logger.info('Starting to add section')
    insert_query = f"""
    INSERT INTO Section (SectionNumber, CourseCode, InstructorID, MaxEnrollment, CurrentEnrollment, Waitlist, SectionStatus) VALUES ({section_number}, '{course_code}', {instructor_id}, {max_enrollment}, 0, 0, 'open')
    """
    cursor = db_connection.cursor()
    cursor.execute("BEGIN")
    try:
        cursor.execute(insert_query)
        cursor.execute("COMMIT")
    except Exception as err:
        logger.error(err)
        cursor.execute("ROLLBACK")
        logger.info('Rolling back transaction')
        raise DBException(error_detail = 'Fail to add section')
    finally:
        cursor.close()

    return QueryStatus.SUCCESS

def deleteSection(db_connection: Connection, course_code: str, section_number: int) -> str:
    logger.info('Starting to delete section')
    delete_query = f"""
    DELETE FROM Section WHERE CourseCode = '{course_code}' and SectionNumber = {section_number}
    """

    cursor = db_connection.cursor()
    cursor.execute("BEGIN")
    try:
        cursor.execute(delete_query)
        cursor.execute("COMMIT")
    except Exception as err:
        logger.error(err)
        cursor.execute("ROLLBACK")
        logger.info('Rolling back transaction')
        raise DBException(error_detail = 'Fail to delete section')
    finally:
        cursor.close()

    return QueryStatus.SUCCESS

def changeSectionInstructor(db_connection: Connection, course_code: str, section_number: int, instructor_id: int) -> str:
    logger.info('Starting to change instructor for section ', str(section_number))
    update_query = f"""
    UPDATE Section SET InstructorID = {instructor_id} WHERE SectionNumber = {section_number} and CourseCode = '{course_code}'
    """

    cursor = db_connection.cursor()
    cursor.execute("BEGIN")
    try:
        cursor.execute(update_query)
        cursor.execute("COMMIT")
    except Exception as err:
        logger.error(err)
        cursor.execute("ROLLBACK")
        logger.info('Rolling back transaction')
        raise DBException(error_detail = 'Fail to change instructor')
    finally:
        cursor.close()

    return QueryStatus.SUCCESS

def freezeEnrollment(db_connection: Connection, course_code: str, section_number: int) -> str:
    logger.info('Starting to freeze enrollment for section ', str(section_number))
    update_query = f"""
    UPDATE Section SET SectionStatus = 'closed' WHERE SectionNumber = {section_number} and CourseCode = '{course_code}'
    """

    cursor = db_connection.cursor()
    cursor.execute("BEGIN")
    try:
        cursor.execute(update_query)
        cursor.execute("COMMIT")
    except Exception as err:
        logger.error(err)
        cursor.execute("ROLLBACK")
        logger.info('Rolling back transaction')
        raise DBException(error_detail = 'Fail to freeze enrollment')
    finally:
        cursor.close()

    return QueryStatus.SUCCESS

# enrolled students
def get_enrolled_students(db_connection: Connection, instructor_id: int, course_code: Optional[str] = None, section_number: Optional[int] = None) -> List[EnrollmentListResponse]:
    logger.info('Getting enrolled students for instructor with CWID:')
    query = """
                SELECT
                    Users.CWID AS StudentCWID,
                    Users.Name AS StudentFirstName,
                    Users.LastName AS StudentLastName,
                    Class.CourseCode AS CourseCode,
                    Section.SectionNumber AS SectionNumber,
                    Class.Name AS ClassName,
                    RegistrationList.Status AS Status
                FROM
                    RegistrationList
                    JOIN Users ON RegistrationList.StudentID = Users.CWID
                    JOIN Section ON RegistrationList.CourseCode = Section.CourseCode AND RegistrationList.SectionNumber = Section.SectionNumber
                    JOIN Class ON Section.CourseCode = Class.CourseCode
                WHERE
                    Section.InstructorID = ?
                    AND RegistrationList.Status = 'enrolled'
            """
    params = [instructor_id]
    if course_code is not None:
        query += " AND Section.CourseCode = ?"
        params.append(course_code)
    if section_number is not None:
        query += " AND Section.SectionNumber = ?"
        params.append(section_number)
    else:
        query += " ORDER BY Class.CourseCode, Section.SectionNumber, Users.LastName, Users.Name"
    cur = db_connection.execute(query, tuple(params))
    enrollment = cur.fetchall()
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment for instructor not found"
        )
    results = [{"student_cwid": row[0],
                      "student_first_name": row[1],
                      "student_last_name": row[2],
                      "course_code": row[3],
                      "section_number": row[4],
                      "class_name": row[5],
                      "status": row[6]} for row in enrollment]
    return results

# waitlisted students
def get_waitlisted_students(db_connection: Connection, instructor_id: int, course_code: Optional[str] = None, section_number: Optional[int] = None) -> List[EnrollmentListResponse]:
    logger.info('Getting enrolled students for instructor with CWID:')
    query = """
                SELECT
                    Users.CWID AS StudentCWID,
                    Users.Name AS StudentFirstName,
                    Users.LastName AS StudentLastName,
                    Class.CourseCode AS CourseCode,
                    Section.SectionNumber AS SectionNumber,
                    Class.Name AS ClassName,
                    RegistrationList.Status AS Status
                FROM
                    RegistrationList
                    JOIN Users ON RegistrationList.StudentID = Users.CWID
                    JOIN Section ON RegistrationList.CourseCode = Section.CourseCode AND RegistrationList.SectionNumber = Section.SectionNumber
                    JOIN Class ON Section.CourseCode = Class.CourseCode
                WHERE
                    Section.InstructorID = ?
                    AND RegistrationList.Status = 'waitlisted'
            """
    params = [instructor_id]
    if course_code is not None:
        query += " AND Section.CourseCode = ?"
        params.append(course_code)
    if section_number is not None:
        query += " AND Section.SectionNumber = ?"
        params.append(section_number)
    else:
        query += " ORDER BY Class.CourseCode, Section.SectionNumber, Users.LastName, Users.Name"
    cur = db_connection.execute(query, tuple(params))
    enrollment = cur.fetchall()
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Waitlist for instructor not found"
        )
    results = [{"student_cwid": row[0],
                      "student_first_name": row[1],
                      "student_last_name": row[2],
                      "course_code": row[3],
                      "section_number": row[4],
                      "class_name": row[5],
                      "status": row[6]} for row in enrollment]
    return results

# dropped students 
def get_dropped_students(db_connection: Connection, instructor_id: int,course_code: Optional[str] = None, section_number: Optional[int] = None) -> List[EnrollmentListResponse]:
    logger.info('Getting dropped students for instructor')
    query = """
                SELECT
                    Users.CWID AS StudentCWID,
                    Users.Name AS StudentFirstName,
                    Users.LastName AS StudentLastName,
                    Class.CourseCode AS CourseCode,
                    Section.SectionNumber AS SectionNumber,
                    Class.Name AS ClassName,
                    RegistrationList.Status AS Status
                FROM
                    RegistrationList
                    JOIN Users ON RegistrationList.StudentID = Users.CWID
                    JOIN Section ON RegistrationList.CourseCode = Section.CourseCode AND RegistrationList.SectionNumber = Section.SectionNumber
                    JOIN Class ON Section.CourseCode = Class.CourseCode
                WHERE
                    Section.InstructorID = ?
                    AND RegistrationList.Status = 'dropped' 
            """
    params = [instructor_id]
    if course_code is not None:
        query += " AND Section.CourseCode = ?"
        params.append(course_code)
    if section_number is not None:
        query += " AND Section.SectionNumber = ?"
        params.append(section_number)
    else:
        query += " ORDER BY Class.CourseCode, Section.SectionNumber, Users.LastName, Users.Name"
    cur = db_connection.execute(query, tuple(params))
    enrollment = cur.fetchall()
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No students that dropped found for instructor"
        )
    results = [{"student_cwid": row[0],
                      "student_first_name": row[1],
                      "student_last_name": row[2],
                      "course_code": row[3],
                      "section_number": row[4],
                      "class_name": row[5],
                      "status": row[6]} for row in enrollment]
    return results

def get_waitlist_status(db_connection: Connection, student_id: int) -> str:
    logger.info('Checking waitlist position for student ', str(student_id))
    query = f"""
        WITH WaitlistPosition AS (
        SELECT
            rl.StudentID,
            rl.CourseCode,
            rl.SectionNumber,
            rl.Status,
            ROW_NUMBER() OVER (PARTITION BY rl.CourseCode, rl.SectionNumber ORDER BY rl.EnrollmentDate) AS Position
        FROM
            RegistrationList rl
        WHERE
            rl.Status = 'waitlisted'
        )
        SELECT
            wlp.Position,
            wlp.CourseCode,
            wlp.SectionNumber
        FROM
            WaitlistPosition wlp
        WHERE
            wlp.StudentID = {student_id}
    """
    cursor = db_connection.cursor()
    rows =  cursor.execute(query)
    if rows.arraysize == 0:
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail= f'Record not found.')
    result = []
    for row in rows:
        logger.info(str(row))
        waitlist = WaitlistPositionList(
            waitlist_position = row[0],
            section_number = row[2],
            course_code = row[1]
        )
        result.append(waitlist)
    print(result)
    return result

def get_waitlist(db_connection: Connection, course_code: str, section_number: int) -> list:
    logger.info(f'fetching  the students on the waitlist with coursecode and section no {course_code}, {section_number}')
    query = f"""
        SELECT
            r.StudentID,
            u.Name AS StudentName,
            r.EnrollmentDate,
            r.Status
        FROM
            RegistrationList r
        JOIN
            Users u ON r.StudentID = u.CWID
        WHERE
            r.CourseCode = "{course_code}"
            AND r.SectionNumber = {section_number}
            AND r.Status = 'waitlisted'
        ORDER BY
            r.EnrollmentDate;
    """
    cursor = db_connection.cursor()
    rows =  cursor.execute(query)
    if rows.arraysize == 0:
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail= f'Records not found.')
        # todo: throw appropriate error messages
    result = []
    for row in rows:
        logger.info(str(row))
        student = WaitlistStudents(
            student_id = row[0],
            student_name = row[1],
            enrollment_date = row[2]
        )
        result.append(student)
    logger.info(result)
    return result

# check if student is enrolled 
def check_is_enrolled(db_connection, DropRequest) -> bool:
    query = """SELECT Status FROM RegistrationList WHERE StudentID = ? AND CourseCode = ? AND SectionNumber = ?"""
    cursor = db_connection.cursor()
    cursor.execute(query, (DropRequest.student_id, DropRequest.course_code, DropRequest.section_number))
    result = cursor.fetchone()
    if result is not None and (result[0] == "enrolled" or result[0] == "waitlisted"):
        return True
    else:
        return False
    
# check if instructor is the instructor of the section 
def check_is_instructor_of_section(db_connection, DropRequest) -> bool:
    query = """SELECT InstructorID FROM Section WHERE CourseCode = ? AND SectionNumber = ?"""
    cursor = db_connection.cursor()
    cursor.execute(query, (DropRequest.course_code, DropRequest.section_number))
    result = cursor.fetchone()
    if result is not None and result[0] == DropRequest.instructor_id:
        return True
    else:
        return False

# drop a student 
def drop_student(db_connection: Connection, DropRequest: DropStudentRequest) -> str:
    logger.info('Dropping student')
    drop = """
                UPDATE RegistrationList SET Status = 'dropped' WHERE StudentID = ? AND CourseCode = ? AND SectionNumber = ?
    """
    update_enrollment = """
                UPDATE Section SET CurrentEnrollment = CurrentEnrollment - 1 WHERE CourseCode = ? AND SectionNumber = ?
    """
    params = [DropRequest.student_id, DropRequest.course_code, DropRequest.section_number]
    cursor = db_connection.cursor()
    cursor.execute("BEGIN")
    try:
        cursor.execute(drop, tuple(params))
        cursor.execute(update_enrollment, (DropRequest.course_code, DropRequest.section_number))
        cursor.execute("COMMIT")
    except Exception as err:
        logger.error(err)
        cursor.execute("ROLLBACK")
        logger.info('Rolling back transaction')
        raise DBException(error_detail = 'Fail to drop student')
    finally:
        cursor.close()
    return QueryStatus.SUCCESS
