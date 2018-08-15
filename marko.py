from ortools.sat.python import cp_model


class SchoolSchedulingProblem(object):

  def __init__(self, subjects, teachers, curriculum, specialties, working_days,
               levels, sections, teacher_work_hours):
    self.subjects = subjects
    self.teachers = teachers
    self.curriculum = curriculum
    self.specialties = specialties
    self.working_days = working_days
    self.levels = levels
    self.sections = sections
    self.teacher_work_hours = teacher_work_hours


class SchoolSchedulingSatSolver(object):

  def __init__(self, problem):
    # Problem
    self.problem = problem

    # Utilities
    self.timeslots = problem.working_days
    
    self.num_days = len(problem.working_days)
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
              # print(name)
              self.assignment[c, s, t, slot] = self.model.NewBoolVar(name)
            else:
              name = 'NO DISP C:{%i} S:{%i} T:{%i} Slot:{%i}' % (c, s, t, slot)
              # print(name)
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
          sum([self.assignment[c, s, teacher, slot] for c in all_courses
              for s in all_subjects for slot in all_slots
          ]) <= self.problem.teacher_work_hours[teacher])

    # Teacher makes all the classes of a subject's course
    # teacher_courses = {}
    # for level in all_levels:
    #   for section in all_sections:
    #     course = level * self.num_sections + section
    #     for subject in all_subjects:
    #       for t in all_teachers:
    #         name = 'C:{%i} S:{%i} T:{%i}' % (course, subject, teacher)
    #         teacher_courses[course, subject, t] = self.model.NewBoolVar(name)
    #         temp_array = [
    #             self.assignment[course, subject, t, slot] for slot in all_slots
    #         ]
    #         self.model.AddMaxEquality(teacher_courses[course, subject, t],
    #                                   temp_array)
    #       self.model.Add(
    #           sum(teacher_courses[course, subject, t]
    #               for t in all_teachers) == 1)

    # Solution collector
    self.collector = None

  def solve(self):
    print('Solving')
    a_few_solutions = [1, 2, 100, 1000, 5000, 50000, 100000, 2000000]

    solver = cp_model.CpSolver()
    solution_printer = SchoolSchedulingSatSolutionPrinter(self.assignment, self.problem.working_days, self.timeslots,
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

  def __init__(self, assignment, working_days, timeslots, teachers, subjects, levels, sections, num_courses, sols):

    self.__working_days = working_days
    self.__slots = timeslots
    self.__teachers = teachers
    self.__subjects = subjects
    self.__levels = levels
    self.__sections = sections

    self.__assignment = assignment
    self.__num_days = len(working_days)
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
  subjects = ['RMC Body/ED', 'RMC Mamm/Breast', 'RMC US/PET/ED', 'RMC Dx4', 'RMC IR', 'SJH Dx/IR',
              'SJH PCAC Dx/Mammo', 'SFH Mamm/Neuro', 'SFH ER/Flouro/Nuclear', 'SFH IR', 'SFH Body/Chest']
  levels = ['1-']
  sections = ['A']
  teachers = ['Lum', 'Iwanik', 'Granato',
              'Clemins', 'Radich', 'Bahu',
              'Rapoport M', 'Rapoport L', 'Brack',
              'Reich', 'Simon', 'Skezas',
              'Calandra', 'Cronin', 'Major',
              'Kim', 'Hamblin']
  teachers_work_hours = [3, 3, 3,
                        4, 4, 4,
                        4, 4, 4,
                        4, 5, 5,
                        4, 4, 4,
                        4, 5]
  working_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

  # This curriculum needs to match up with the right amount of specialties
  # For example, this won't work:
  #  Having one person specialize solo in two departments. If we alott 5 hours to each employee, this person cant be at two depts at once
  curriculum = {
      ('1-', 'RMC Body/ED'): 5,
      ('1-', 'RMC Mamm/Breast'): 5,
      ('1-', 'RMC US/PET/ED'): 5,
      ('1-', 'RMC Dx4'): 5,
      ('1-', 'RMC IR'): 5,
      ('1-', 'SJH Dx/IR'): 5,
      ('1-', 'SJH PCAC Dx/Mammo'): 5,
      ('1-', 'SFH Mamm/Neuro'): 5,
      ('1-', 'SFH ER/Flouro/Nuclear'): 5,
      ('1-', 'SFH IR'): 5,
      ('1-', 'SFH Body/Chest'): 5
  }

  # Subject -> List of teachers who can teach it
  specialties_idx_inverse = [
      [0, 1, 2, 3],      # RMC Body/ED
      [2, 3, 4],      # RMC Mamm/Breast
      [0, 6],      # RMC US/PET/ED
      [0, 4, 7, 8],      # RMC Dx4
      [3, 9],      # RMC IR
      [10],      # SJH Dx/IR
      [11],      # SJH PCAC Dx/Mammo
      [12, 13, 14],      # SFH Mamm/Neuro
      [13, 14, 15],     # SFH ER/Flouro/Nuclear
      [16],      # SFH IR
      [12, 13, 14]      # SFH Body/Chest
  ]
  


  problem = SchoolSchedulingProblem(
      subjects, teachers, curriculum, specialties_idx_inverse, working_days,
      levels, sections, teachers_work_hours)
  solver = SchoolSchedulingSatSolver(problem)
  solver.solve()
  solver.print_status()


if __name__ == '__main__':
  main()
