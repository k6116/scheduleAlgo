"""I'm trying to solve a school scheduling problem using the SAT solver. Since is similar to the nurse scheduling problem (https://github.com/google/or-tools/blob/master/examples/python/nurses_sat.py)  I used a similar approach, but I'm having some trouble with a constraint, I would like to ask you for your guidance since i've been stuck for a while now.
In this problem I have courses, subjects, teachers and timeslots. , A course is made of a level (first grade, second grade, etc) and a section (A, B), for example 1°A, 1°B, 2°A, ...., subjects are Math, English, History, etc, We have t Teachers, each one with some skills that allow them to teach some subjects and the timeslots are when the subjects are taught. Also, every level contains a curriculum, that is the quantity of timeslots per subject required, for example all the first grades need to have 5 timeslots of english, 3 of math, and so on.
So we have some restrictions:
+ A teacher cannot teach more than 1 class simultaneosly
+ A teacher can only teach subjects of his/her set of skills (specialties)
+ Each course must meet the quantity of classes speicfied in the curriculum
+ Each teacher has a maximum number of working hours (here hours == timeslots)
- For a given course and subject, the teacher must be the same for all of them (ex: 1°A has only one Math teacher)
I modeled the problem as a big boolean matrix: assign[c, s, t, ts] = 1 if teacher t is assigned to course c and subject s in timeslot ts, and I've been able to add all the constraints but the last one."""

from ortools.sat.python import cp_model


class SchoolSchedulingProblem(object):

  def __init__(self, subjects, teachers, curriculum, specialties, working_days,
               periods, levels, sections, teacher_work_hours):
    self.subjects = subjects
    self.teachers = teachers
    self.curriculum = curriculum
    self.specialties = specialties
    self.working_days = working_days
    self.periods = periods
    self.levels = levels
    self.sections = sections
    self.teacher_work_hours = teacher_work_hours


class SchoolSchedulingSatSolver(object):

  def __init__(self, problem):
    # Problem
    self.problem = problem

    # Utilities
    self.timeslots = [
        '{0:10} {1:6}'.format(x, y)
        for x in problem.working_days
        for y in problem.periods
    ]
    
    self.num_days = len(problem.working_days)
    self.num_periods = len(problem.periods)
    self.num_slots = len(self.timeslots)
    self.num_teachers = len(problem.teachers)
    self.num_subjects = len(problem.subjects)
    self.num_levels = len(problem.levels)
    self.num_sections = len(problem.sections)
    self.courses = [
        x * self.num_levels + y
        for x in problem.levels
        for y in problem.sections
    ]
    self.num_courses = self.num_levels * self.num_sections

    all_courses = range(self.num_courses)
    all_teachers = range(self.num_teachers)
    all_slots = range(self.num_slots)
    all_sections = range(self.num_sections)
    all_subjects = range(self.num_subjects)
    all_levels = range(self.num_levels)

    self.model = cp_model.CpModel()

    self.assignment = {}
    for c in all_courses:
      for s in all_subjects:
        for t in all_teachers:
          for slot in all_slots:
            if t in self.problem.specialties[s]:
              name = 'C:{%i} S:{%i} T:{%i} Slot:{%i}' % (c, s, t, slot)
              self.assignment[c, s, t, slot] = self.model.NewBoolVar(name)
            else:
              name = 'NO DISP C:{%i} S:{%i} T:{%i} Slot:{%i}' % (c, s, t, slot)
              self.assignment[c, s, t, slot] = self.model.NewIntVar(0, 0, name)

    # Constraints

    # Each course must have the quantity of classes specified in the curriculum
    for level in all_levels:
      for section in all_sections:
        course = level * self.num_sections + section
        for subject in all_subjects:
          required_slots = self.problem.curriculum[self.problem.levels[
              level], self.problem.subjects[subject]]
          self.model.Add(
              sum(self.assignment[course, subject, teacher, slot]
                  for slot in all_slots
                  for teacher in all_teachers) == required_slots)

    # Teacher can do at most one class at a time
    for teacher in all_teachers:
      for slot in all_slots:
        self.model.Add(
            sum([
                self.assignment[c, s, teacher, slot]
                for c in all_courses
                for s in all_subjects
            ]) <= 1)

    # Maximum work hours for each teacher
    for teacher in all_teachers:
      self.model.Add(
          sum([
              self.assignment[c, s, teacher, slot] for c in all_courses
              for s in all_subjects for slot in all_slots
          ]) <= self.problem.teacher_work_hours[teacher])

    # Teacher makes all the classes of a subject's course
    teacher_courses = {}
    for level in all_levels:
      for section in all_sections:
        course = level * self.num_sections + section
        for subject in all_subjects:
          for t in all_teachers:
            name = 'C:{%i} S:{%i} T:{%i}' % (course, subject, teacher)
            teacher_courses[course, subject, t] = self.model.NewBoolVar(name)
            temp_array = [
                self.assignment[course, subject, t, slot] for slot in all_slots
            ]
            self.model.AddMaxEquality(teacher_courses[course, subject, t],
                                      temp_array)
          self.model.Add(
              sum(teacher_courses[course, subject, t]
                  for t in all_teachers) == 1)

    # Solution collector
    self.collector = None

  def solve(self):
    print('Solving')
    a_few_solutions = [1, 2, 100, 1000, 5000, 50000, 100000, 2000000]

    solver = cp_model.CpSolver()
    solution_printer = SchoolSchedulingSatSolutionPrinter(self.assignment, self.problem.working_days, self.problem.periods, self.timeslots,
      self.problem.teachers, self.problem.subjects, self.problem.levels, self.problem.sections, self.num_courses, a_few_solutions)
    status = solver.SearchForAllSolutions(self.model, solution_printer)
    print('- Statistics')
    print('  - Branches', solver.NumBranches())
    print('  - Conflicts', solver.NumConflicts())
    print('  - WallTime', solver.WallTime())
    print('  - solutions found : %i' % solution_printer.SolutionCount())

  def print_status(self):
    pass


class SchoolSchedulingSatSolutionPrinter(cp_model.CpSolverSolutionCallback):

  def __init__(self, assignment, working_days, periods, timeslots, teachers, subjects, levels, sections, num_courses, sols):

    self.__working_days = working_days
    self.__periods = periods
    self.__slots = timeslots
    self.__teachers = teachers
    self.__subjects = subjects
    self.__levels = levels
    self.__sections = sections

    self.__assignment = assignment
    self.__num_days = len(working_days)
    self.__num_periods = len(periods)
    self.__num_slots = len(timeslots)
    self.__num_teachers = len(teachers)
    self.__num_subjects = len(subjects)
    self.__num_levels = len(levels)
    self.__num_sections = len(sections)
    self.__num_courses = self.__num_levels * self.__num_sections
    self.__solutions = set(sols)
    self.__solution_count = 0

  def NewSolution(self):
    self.__solution_count += 1
    if self.__solution_count in self.__solutions:
      print('\n')
      print('Solution #%i' % self.__solution_count)
      
      for c in range(self.__num_courses):
        for s in range(self.__num_subjects):
          for t in range(self.__num_teachers):
            for ts in range(self.__num_slots):
              if self.Value(self.__assignment[(c, s, t, ts)]):
                subject_name = self.__subjects[s]
                teacher_name = self.__teachers[t]
                slot_name = self.__slots[ts]
                print(' Course #%i | Subject #%s | Teacher #%s | TimeSlot #%s' % (c, subject_name, teacher_name, slot_name))
      print('\n')

  def SolutionCount(self):
    return self.__solution_count


def main():
  # DATA
  subjects = ['English', 'Math', 'History']
  levels = ['1-', '2-', '3-']
  sections = ['A']
  teachers = ['Mario', 'Elvis', 'Donald', 'Ian']
  teachers_work_hours = [18, 12, 12, 18]
  working_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
  periods = ['08:00-09:30', '09:45-11:15', '11:30-13:00']
  curriculum = {
      ('1-', 'English'): 5,
      ('1-', 'Math'): 3,
      ('1-', 'History'): 2,
      ('2-', 'English'): 4,
      ('2-', 'Math'): 2,
      ('2-', 'History'): 2,
      ('3-', 'English'): 2,
      ('3-', 'Math'): 4,
      ('3-', 'History'): 2
  }
  # Subject -> List of teachers who can teach it
  specialties_idx_inverse = [
      [1, 3],  # English   -> Elvis & Ian
      [0, 3],  # Math      -> Mario & Ian
      [2, 3]  # History   -> Donald & Ian
  ]
  
  # subjects = ['English', 'Math']
  # levels = ['1-']
  # sections = ['A']
  # teachers = ['Mario', 'Elvis']
  # teachers_work_hours = [18, 12]
  # working_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
  # periods = ['08:00-09:30']
  # curriculum = {
  #   ('1-', 'English'): 3,
  #   ('1-', 'Math'): 3
  # }
  # specialties_idx_inverse = [
  #     [0],  # English   -> Elvis & Ian
  #     [1]  # Math      -> Mario & Ian
  # ]

 

  problem = SchoolSchedulingProblem(
      subjects, teachers, curriculum, specialties_idx_inverse, working_days,
      periods, levels, sections, teachers_work_hours)
  solver = SchoolSchedulingSatSolver(problem)
  solver.solve()
  solver.print_status()


if __name__ == '__main__':
  main()
