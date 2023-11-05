-- classes.sql

PRAGMA foreign_keys=ON;
BEGIN TRANSACTION;

-- Create the Users table
DROP TABLE IF EXISTS Users;
CREATE TABLE IF NOT EXISTS Users (
    CWID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT NOT NULL,
    Middle TEXT NULL,
    LastName TEXT NOT NULL,
    Role TEXT NOT NULL CHECK (role IN ('Instructor', 'Registrar', 'Student'))
);

-- Create the Class table
DROP TABLE IF EXISTS Class;
CREATE TABLE IF NOT EXISTS Class (
    CourseCode TEXT PRIMARY KEY,
    Name TEXT NOT NULL,
    Department TEXT NOT NULL
);

-- Create the Section table
DROP TABLE IF EXISTS Section;
CREATE TABLE IF NOT EXISTS Section (
    SectionNumber INTEGER NOT NULL,
    CourseCode TEXT NOT NULL,
    InstructorID INTEGER NOT NULL,
    CurrentEnrollment INTEGER NOT NULL,
    MaxEnrollment INTEGER NOT NULL,
    Waitlist INTEGER NOT NULL,
    SectionStatus TEXT NOT NULL CHECK (SectionStatus IN ('open', 'closed')),
    PRIMARY KEY (SectionNumber, CourseCode),
    FOREIGN KEY (CourseCode) REFERENCES Class (CourseCode),
    FOREIGN KEY (InstructorID) REFERENCES Users (CWID)
);


-- Create the RegistrationList table
DROP TABLE IF EXISTS RegistrationList;
CREATE TABLE IF NOT EXISTS RegistrationList (
    RecordID INTEGER PRIMARY KEY AUTOINCREMENT,
    StudentID INTEGER NOT NULL,
    CourseCode TEXT NOT NULL,
    SectionNumber INTEGER NOT NULL,
    EnrollmentDate DATETIME DEFAULT (CURRENT_TIMESTAMP),
    Status TEXT NOT NULL CHECK (Status IN ('enrolled', 'waitlisted', 'dropped')),
    FOREIGN KEY (StudentID) REFERENCES Users (CWID),
    FOREIGN KEY (CourseCode, SectionNumber) REFERENCES Section (CourseCode, SectionNumber)
);

-- pre populate database 
-- chatGPT was used to generate some of the data
-- Users Table
INSERT INTO Users (Name, Middle, LastName, Role) VALUES
    ('Emily', NULL, 'Davis' ,'Registrar'),
    ('John', 'A.', 'Smith', 'Instructor'),
    ('Jane', 'M.', 'Doe' ,'Instructor'),
    ('Robert', 'E.', 'Johnson', 'Instructor'),
    ('Mark', 'B.', 'Johnson', 'Instructor'),
    ('Catherine', 'E.', 'Wilson', 'Instructor'),
    ('Matthew', 'J.', 'Davis', 'Instructor'),
    ('Jennifer', 'R.', 'Harris', 'Instructor'),
    ('Kevin', 'W.', 'Smith', 'Instructor'),
    ('Linda', 'A.', 'Williams', 'Instructor'),
    ('Michael', 'J.', 'Wilson', 'Student'),
    ('Susan', 'K.', 'Brown', 'Student'),
    ('David', 'P.', 'Miller', 'Student'),
    ('Jennifer', NULL, 'Clark', 'Student'),
    ('Richard', 'R.', 'White', 'Student'),
    ('Sarah', 'L.', 'Anderson', 'Student'),
    ('William', 'T.', 'Lee', 'Student'),
    ('Karen', NULL, 'Martinez', 'Student'),
    ('Thomas', 'S.', 'Taylor', 'Student'),
    ('Laura', 'M.', 'Garcia', 'Student'),
    ('Steven', NULL, 'Harris', 'Student'),
    ('Daniel', 'M.', 'Wilson', 'Student'),
    ('Michelle', 'L.', 'Johnson', 'Student'),
    ('Christopher', 'S.', 'Brown', 'Student'),
    ('Jessica', NULL, 'Anderson', 'Student'),
    ('Jason', 'D.', 'Turner', 'Student'),
    ('Melissa', NULL, 'Adams', 'Student'),
    ('Paul', 'R.', 'Robinson', 'Student'),
    ('Jessica', 'A.', 'Miller', 'Student'),
    ('Brian', NULL, 'Thompson', 'Student'),
    ('Sandra', 'N.', 'Davis', 'Student'),
    ('Eric', 'P.', 'Smith', 'Student'),
    ('Rachel', NULL, 'Evans', 'Student'),
    ('George', 'W.', 'Parker', 'Student'),
    ('Lisa', 'K.', 'Hernandez', 'Student');

-- Class Table
INSERT INTO Class (CourseCode, Name, Department) VALUES
    ('CPSC-101', 'Introduction to Programming', 'Computer Science'),
    ('CPSC-111', 'Data Structures and Algorithms', 'Computer Science'),
    ('MATH-201', 'Calculus I', 'Mathematics'),
    ('PHYS-301', 'Physics for Engineers', 'Physics'),
    ('PYS-101', 'Introduction to Psychology', 'Psychology'),
    ('ENG-541', 'English Composition', 'English'),
    ('ART-271', 'Art History', 'Art'),
    ('CHEM-101', 'Introduction to Chemistry', 'Chemistry'),
    ('HIST-281', 'World History', 'History'),
    ('ECON-554', 'Microeconomics', 'Economy'),
    ('BIOL-211', 'Cell Biology', 'Biology'),
    ('CHEM-301', 'Organic Chemistry', 'Chemistry'),
    ('MATH-202', 'Calculus II', 'Mathematics'),
    ('PHYS-201', 'Classical Mechanics', 'Physics'),
    ('SOC-101', 'Introduction to Sociology', 'Sociology'),
    ('BUS-401', 'Marketing Management', 'Business'),
    ('ENG-321', 'Creative Writing', 'English'),
    ('PHIL-101', 'Introduction to Philosophy', 'Philosophy'),
    ('ART-352', 'Modern Art', 'Art'),
    ('HIST-381', 'European History', 'History'),
    ('ECON-301', 'Macroeconomics', 'Economy'),
    ('PSYCH-201', 'Abnormal Psychology', 'Psychology'),
    ('SOC-201', 'Social Problems', 'Sociology'),
    ('CHEM-202', 'Analytical Chemistry', 'Chemistry'),
    ('MATH-301', 'Linear Algebra', 'Mathematics'),
    ('PHYS-401', 'Quantum Mechanics', 'Physics'),
    ('BUS-201', 'Financial Accounting', 'Business'),
    ('ENG-431', 'American Literature', 'English'),
    ('PHIL-202', 'Ethics', 'Philosophy'),
    ('ART-413', 'Renaissance Art', 'Art');

-- Section Table
INSERT INTO Section (sectionNumber, CourseCode, InstructorID, CurrentEnrollment, MaxEnrollment, Waitlist, SectionStatus) VALUES
    (1, 'CPSC-101', 2, 5, 30, 1, 'closed'),
    (2, 'CPSC-101', 2, 4, 30, 1, 'open'),
    (1, 'CPSC-111', 2, 2, 35, 1, 'open'),
    (2, 'CPSC-111', 7, 3, 25, 0, 'open'),
    (5, 'MATH-201', 3, 0, 25, 0, 'open'),
    (1, 'MATH-201', 8, 3, 30, 0, 'open'),
    (2, 'MATH-201', 9, 2, 20, 1, 'open'),
    (1, 'PHYS-301', 3, 4, 20, 0, 'open'),
    (2, 'PHYS-301', 10, 4, 35, 0, 'open'),
    (1, 'PYS-101', 2, 6, 35, 0, 'open'),
    (2, 'PYS-101', 6, 4, 25, 0, 'open'),
    (1, 'ENG-541', 7, 2, 25, 1, 'open'),
    (2, 'ENG-541', 8, 1, 30, 0, 'open'),
    (1, 'ART-271', 9, 1, 20, 0, 'open'),
    (2, 'ART-271', 10, 0, 35, 0, 'open'),
    (1, 'CHEM-101', 4, 1, 30, 0, 'open'),
    (2, 'CHEM-101', 5, 0, 25, 1, 'open'),
    (1, 'HIST-281', 6, 0, 35, 0, 'open'),
    (2, 'HIST-281', 7, 0, 20, 0, 'open'),
    (1, 'ECON-554', 8, 2, 30, 0, 'open'),
    (2, 'ECON-554', 9, 0, 25, 0, 'open'),
    (1, 'BIOL-211', 10, 2, 20, 0, 'open'),
    (2, 'BIOL-211', 4, 0, 35, 0, 'open'),
    (1, 'CHEM-301', 5, 0, 30, 0, 'open'),
    (2, 'CHEM-301', 6, 0, 25, 0, 'open'),
    (1, 'MATH-202', 7, 3, 35, 0, 'open'),
    (2, 'MATH-202', 8, 2, 20, 0, 'open'),
    (1, 'PHYS-201', 9, 2, 30, 0, 'open'),
    (2, 'PHYS-201', 10, 0, 25, 0, 'open'),
    (1, 'SOC-101', 4, 2, 25, 0, 'open'),
    (2, 'SOC-101', 5, 2, 30, 0, 'open'),
    (1, 'BUS-401', 6, 0, 20, 0, 'open'),
    (2, 'BUS-401', 7, 0, 35, 0, 'open'),
    (1, 'ENG-321', 8, 0, 30, 0, 'open'),
    (2, 'ENG-321', 9, 0, 25, 0, 'open'),
    (1, 'PHIL-101', 10, 0, 35, 0, 'open'),
    (2, 'PHIL-101', 4, 0, 20, 0, 'open'),
    (1, 'ART-352', 5, 0, 30, 0, 'open'),
    (2, 'ART-352', 6, 0, 25, 0, 'open'),
    (1, 'HIST-381', 7, 0, 25, 0, 'open'),
    (2, 'HIST-381', 8, 0, 30, 0, 'open'),
    (1, 'ECON-301', 9, 0, 20, 0, 'open'),
    (2, 'ECON-301', 10, 0, 35, 0, 'open'),
    (1, 'PSYCH-201', 4, 0, 30, 0, 'open'),
    (2, 'PSYCH-201', 5, 0, 25, 0, 'open'),
    (1, 'SOC-201', 6, 0, 35, 0, 'open'),
    (2, 'SOC-201', 7, 0, 20, 0, 'open'),
    (1, 'CHEM-202', 8, 0, 30, 0, 'open'),
    (2, 'CHEM-202', 9, 0, 25, 0, 'open'),
    (1, 'MATH-301', 10, 1, 20, 0, 'open'),
    (2, 'MATH-301', 4, 2, 35, 0, 'open'),
    (1, 'PHYS-401', 5, 2, 30, 0, 'open'),
    (2, 'PHYS-401', 6, 2, 25, 0, 'open'),
    (1, 'BUS-201', 7, 0, 35, 0, 'open'),
    (2, 'BUS-201', 8, 0, 20, 0, 'open'),
    (1, 'ENG-431', 9, 1, 30, 0, 'open'),
    (2, 'ENG-431', 10, 0, 25, 0, 'open'),
    (1, 'PHIL-202', 4, 2, 25, 0, 'open'),
    (2, 'PHIL-202', 5, 1, 30, 0, 'open'),
    (1, 'ART-413', 6, 0, 20, 1, 'open');

-- RegistrationList Table
INSERT INTO RegistrationList (StudentID, CourseCode, SectionNumber, Status) VALUES
    -- Student 12
    (12, 'CPSC-101', 1, 'enrolled'),
    (12, 'MATH-201', 1, 'enrolled'),
    (12, 'PHYS-301', 1, 'enrolled'),
    (12, 'PYS-101', 1, 'enrolled'),
    (12, 'CPSC-111', 1, 'dropped'),
    
    -- Student 13
    (13, 'CPSC-101', 2, 'enrolled'),
    (13, 'MATH-201', 2, 'enrolled'),
    (13, 'PHYS-301', 2, 'enrolled'),
    (13, 'CPSC-111', 1, 'waitlisted'),
    
    -- Student 14
    (14, 'CPSC-101', 1, 'enrolled'),
    (14, 'MATH-201', 1, 'enrolled'),
    (14, 'PHYS-301', 1, 'enrolled'),
    (14, 'CPSC-111', 2, 'dropped'),
    
    -- Student 15
    (15, 'CPSC-111', 1, 'enrolled'),
    (15, 'PHYS-301', 1, 'enrolled'),
    (15, 'PYS-101', 1, 'enrolled'),
    (15, 'CPSC-101', 2, 'waitlisted'),
    
    -- Student 16
    (16, 'CPSC-111', 2, 'enrolled'),
    (16, 'MATH-201', 2, 'enrolled'),
    (16, 'PHYS-301', 2, 'enrolled'),
    (16, 'PYS-101', 2, 'enrolled'),
    (16, 'CPSC-101', 1, 'waitlisted'),
    
    -- Student 17
    (17, 'MATH-201', 1, 'enrolled'),
    (17, 'PYS-101', 1, 'enrolled'),
    (17, 'CPSC-101', 2, 'dropped'),
    
    -- Student 18
    (18, 'CPSC-101', 1, 'enrolled'),
    (18, 'PHYS-301', 1, 'enrolled'),
    (18, 'PYS-101', 1, 'enrolled'),
    (18, 'MATH-201', 2, 'waitlisted'),

    -- Student 19
    (19, 'CPSC-101', 1, 'enrolled'),
    (19, 'MATH-202', 1, 'enrolled'),
    (19, 'PHYS-201', 1, 'enrolled'),
    (19, 'PYS-101', 1, 'enrolled'),
    (19, 'CHEM-101', 2, 'waitlisted'),
    
    -- Student 20
    (20, 'CPSC-101', 2, 'enrolled'),
    (20, 'MATH-301', 2, 'enrolled'),
    (20, 'PHYS-401', 2, 'enrolled'),
    (20, 'PYS-101', 2, 'enrolled'),
    (20, 'ENG-541', 1, 'waitlisted'),
    
    -- Student 21
    (21, 'MATH-202', 1, 'enrolled'),
    (21, 'PHYS-201', 1, 'enrolled'),
    (21, 'CHEM-101', 1, 'enrolled'),
    (21, 'ENG-541', 1, 'enrolled'),
    
    -- Student 22
    (22, 'CPSC-101', 2, 'enrolled'),
    (22, 'PHIL-101', 2, 'enrolled'),
    (22, 'SOC-101', 2, 'enrolled'),
    (22, 'MATH-301', 2, 'enrolled'),
    (22, 'PHYS-401', 2, 'enrolled'),
    
    -- Student 23
    (23, 'CPSC-111', 1, 'enrolled'),
    (23, 'ECON-554', 1, 'enrolled'),
    (23, 'BIOL-211', 1, 'enrolled'),
    (23, 'ENG-431', 1, 'enrolled'),
    
    -- Student 24
    (24, 'CPSC-111', 2, 'enrolled'),
    (24, 'PHYS-301', 2, 'enrolled'),
    (24, 'PYS-101', 2, 'enrolled'),
    (24, 'MATH-202', 2, 'enrolled'),
    
    -- Student 25
    (25, 'MATH-301', 1, 'enrolled'),
    (25, 'PHYS-401', 1, 'enrolled'),
    (25, 'SOC-101', 1, 'enrolled'),
    (25, 'PHIL-202', 1, 'enrolled'),
    (25, 'ART-413', 1, 'waitlisted'),
    
    -- Student 26
    (26, 'CPSC-101', 1, 'dropped'),
    (26, 'PHYS-301', 1, 'dropped'),
    (26, 'PYS-101', 1, 'dropped'),
    (26, 'MATH-202', 2, 'enrolled'),
    
    -- Student 27
    (27, 'MATH-301', 2, 'dropped'),
    (27, 'PHYS-401', 2, 'dropped'),
    (27, 'SOC-101', 2, 'enrolled'),
    (27, 'PHIL-202', 2, 'enrolled'),
    
    -- Student 28
    (28, 'CPSC-111', 1, 'dropped'),
    (28, 'ECON-554', 1, 'enrolled'),
    (28, 'BIOL-211', 1, 'enrolled'),
    (28, 'ENG-431', 1, 'dropped'),
    
    -- Student 29
    (29, 'CPSC-111', 2, 'enrolled'),
    (29, 'PHYS-301', 2, 'dropped'),
    (29, 'PYS-101', 2, 'enrolled'),
    (29, 'MATH-202', 2, 'dropped'),
    
    -- Student 30
    (30, 'MATH-301', 1, 'dropped'),
    (30, 'PHYS-401', 1, 'enrolled'),
    (30, 'SOC-101', 1, 'enrolled'),
    (30, 'PHIL-202', 1, 'enrolled'),
    
    -- Student 31
    (31, 'CPSC-101', 2, 'enrolled'),
    (31, 'PHYS-301', 2, 'enrolled'),
    (31, 'PYS-101', 2, 'dropped'),
    (31, 'ENG-541', 2, 'enrolled'),
    
    -- Student 32
    (32, 'CPSC-101', 1, 'enrolled'),
    (32, 'MATH-202', 1, 'enrolled'),
    (32, 'PHYS-201', 1, 'dropped'),
    (32, 'PYS-101', 1, 'enrolled'),
    
    -- Student 33
    (33, 'CHEM-101', 2, 'dropped'),
    (33, 'ENG-541', 1, 'enrolled'),
    (33, 'ART-271', 1, 'enrolled'),
    (33, 'CHEM-301', 1, 'dropped');

COMMIT;
