package timetable

import (
	"archive/zip"
	"fmt"
	"io"
	"math/rand"
	"os"
	"slices"

	"golang.org/x/sync/errgroup"
)

type day uint // 1 (Monday) - 7 (Sunday)

type timeRange struct {
	lowerMinuteCount uint // number of minutes since midnight
	upperMinuteCount uint // number of minutes since midnight
}

type subject struct {
	name  string
	color string // hex code including the '#'
}

type teacher struct {
	id      int
	name    string
	routine map[day][]timeRange
}

type groupRoutineBreak struct {
	name   string
	period timeRange
}

type groupRoutine struct {
	period timeRange
	breaks []groupRoutineBreak // ordered by time range in an ascending order.
}

type groupClassLesson struct {
	subject            *subject
	teacher            *teacher
	maxLessonCount     int // <=0 - unconsidered; > 0 - limit. total count of mandatory specifics should be excluded.
	mandatorySpecifics map[day][]timeRange
}

type groupClassLessonSpecifics struct {
	subject *subject
	teacher *teacher
	period  timeRange
}

type groupClass struct {
	id        int
	name      string
	teacher   *teacher
	lessons   []groupClassLesson
	specifics map[day][]groupClassLessonSpecifics // ordered by time range in an ascending order.
}

type group struct {
	name    string
	routine map[day]groupRoutine
	classes []groupClass

	lessonDurationInMinutes uint
}

type school struct {
	groups []group

	areClassesValid        bool
	areSpecificsValid      bool
	areTimetablesGenerated bool

	baseClassTimetables   []cTimetable // track valid class timetables
	baseTeacherTimetables []tTimetable // track valid teacher timetables

	baseClassEntries   map[int]int // maps class id to its index in the class timetables
	baseTeacherEntries map[int]int // maps teacher id to its index in the teacher timetables
}

func dayName(i day) string {
	switch i {
	case 1:
		return "Monday"
	case 2:
		return "Tuesday"
	case 3:
		return "Wednesday"
	case 4:
		return "Thursday"
	case 5:
		return "Friday"
	case 6:
		return "Saturday"
	default:
		return "Sunday"
	}
}

func checkClassValidity(routine timeRange, occupied []timeRange, lessonDuration uint) bool {
	slices.SortFunc(occupied, func(a, b timeRange) int {
		return int(a.lowerMinuteCount - b.lowerMinuteCount)
	})

	var current int
	start := routine.lowerMinuteCount
	for start != routine.upperMinuteCount {
		for i := current; i < len(occupied); i++ {
			if start > occupied[i].lowerMinuteCount {
				return false
			}
			if start == occupied[i].lowerMinuteCount {
				start = occupied[i].upperMinuteCount
				current++
				continue
			}
			break
		}

		if start > routine.upperMinuteCount {
			return false
		}
		if start < routine.upperMinuteCount {
			start += lessonDuration
		}
	}

	return true
}

// It ensures that the gaps in between the mandatory specifics and breaks for a particular day allow for full lessons of the specified duration.
// Returns human-readable issues including the days & classes.
func (s *school) CheckValidityOfClasses() []string {
	var issues []string
	for groupIdx := range s.groups {
		for classIdx := range s.groups[groupIdx].classes {
			for day, dayRoutine := range s.groups[groupIdx].routine {
				specifics := s.groups[groupIdx].classes[classIdx].specifics[day]
				occupiedperiods := make([]timeRange, 0, len(dayRoutine.breaks)+len(specifics))
				for _, b := range dayRoutine.breaks {
					occupiedperiods = append(occupiedperiods, b.period)
				}
				for i := range specifics {
					occupiedperiods = append(occupiedperiods, specifics[i].period)
				}
				if !checkClassValidity(dayRoutine.period, occupiedperiods, s.groups[groupIdx].lessonDurationInMinutes) {
					issues = append(issues, fmt.Sprintf("class '%v' of the group '%v' has an invalid schedule for the day '%v'.", s.groups[groupIdx].classes[classIdx].name, s.groups[groupIdx].name, dayName(day)))
				}
			}
		}
	}
	s.areClassesValid = len(issues) == 0
	return issues
}

// It ensures that a teacher does not have more than one lesson happening at a given time.
// Returns human-readable issues including the teacher & lesson details.
func (s *school) CheckValidityOfSpecifics() []string {
	var issues []string
	s.baseClassTimetables = nil
	s.baseTeacherTimetables = nil
	s.baseClassEntries = make(map[int]int)
	s.baseTeacherEntries = make(map[int]int)

	var classId int
	for groupIdx := range s.groups {
		for classIdx := range s.groups[groupIdx].classes {
			classId++
			s.groups[groupIdx].classes[classIdx].id = classId

			classEntryIdx, ok := s.baseClassEntries[classIdx]
			if !ok {
				// classes are included irregardless of the presence of breaks & mandatory lessons
				s.baseClassTimetables = append(s.baseClassTimetables, cTimetable{
					id:               s.groups[groupIdx].classes[classIdx].id,
					groupName:        s.groups[groupIdx].name,
					className:        s.groups[groupIdx].classes[classIdx].name,
					classTeacherName: s.groups[groupIdx].classes[classIdx].teacher.name,
				})
				classEntryIdx = len(s.baseClassTimetables) - 1
				s.baseClassEntries[classIdx] = classEntryIdx
			}

			for day, specifics := range s.groups[groupIdx].classes[classIdx].specifics {
				for specificIdx := range specifics {
					s.baseClassTimetables[classEntryIdx].insertNode(
						day, &cTimetableDayNode{
							period:       specifics[specificIdx].period,
							isLesson:     true,
							subjectName:  specifics[specificIdx].subject.name,
							subjectColor: specifics[specificIdx].subject.color,
							teacherName:  specifics[specificIdx].teacher.name,
						},
					)

					teacherEntryIdx, ok := s.baseTeacherEntries[specifics[specificIdx].teacher.id]
					if !ok {
						s.baseTeacherTimetables = append(s.baseTeacherTimetables, tTimetable{
							id:   specifics[specificIdx].teacher.id,
							name: specifics[specificIdx].teacher.name,
						})
						teacherEntryIdx = len(s.baseTeacherTimetables) - 1
						s.baseTeacherEntries[specifics[specificIdx].teacher.id] = teacherEntryIdx
					}
					valid := s.baseTeacherTimetables[teacherEntryIdx].insertNode(day, &tTimetableDayNode{
						subjectName:  specifics[specificIdx].subject.name,
						subjectColor: specifics[specificIdx].subject.color,
						className:    s.groups[groupIdx].classes[classIdx].name,
						period:       specifics[specificIdx].period,
					})
					if !valid {
						teacherId := specifics[specificIdx].teacher.id
						teacherName := specifics[specificIdx].teacher.name
						lower := specifics[specificIdx].period.lowerMinuteCount
						upper := specifics[specificIdx].period.upperMinuteCount
						collisionTime := fmt.Sprintf("%02d:%02d - %02d:%02d", lower/60, lower%60, upper/60, upper%60)
						issues = append(issues, fmt.Sprintf("teacher '%v' with the id '%v' has a mandatory lesson overlapping at '%v' on '%v'.", teacherName, teacherId, collisionTime, dayName(day)))
					}
				}
			}

			for day, routine := range s.groups[groupIdx].routine {
				for breakIdx := range routine.breaks {
					s.baseClassTimetables[classEntryIdx].insertNode(
						day, &cTimetableDayNode{
							period:    routine.breaks[breakIdx].period,
							breakName: routine.breaks[breakIdx].name,
						},
					)
				}
			}
		}
	}
	s.areSpecificsValid = len(issues) == 0
	return issues
}

func (s *school) generateTimetable() bool {
	classTimetables := make([]cTimetable, 0, len(s.baseClassTimetables))
	for i := range s.baseClassTimetables {
		classTimetables = append(classTimetables, s.baseClassTimetables[i].copy())
	}
	teacherTimetables := make([]tTimetable, 0, len(s.baseTeacherTimetables))
	for i := range s.baseTeacherTimetables {
		teacherTimetables = append(teacherTimetables, s.baseTeacherTimetables[i].copy())
	}
	classEntries := make(map[int]int, len(s.baseClassEntries))
	for k, v := range s.baseClassEntries {
		classEntries[k] = v
	}
	teacherEntries := make(map[int]int, len(s.baseTeacherEntries))
	for k, v := range s.baseTeacherEntries {
		teacherEntries[k] = v
	}

	for groupIdx := range s.groups {
		for classIdx := range s.groups[groupIdx].classes {
			classEntryIdx := classEntries[classIdx]

			var validLesssonIndices []int     // tracks the complete list of indices in the availableLessons slice whose lesson count > 0
			teacherLessons := map[int][]int{} // maps teacher id to list of indices in the availableLessons slice
			availableLessons := make([]groupClassLesson, 0, len(s.groups[groupIdx].classes[classIdx].lessons))
			for _, lesson := range s.groups[groupIdx].classes[classIdx].lessons {
				if lesson.maxLessonCount > 0 {
					availableLessons = append(availableLessons, lesson)
					validLesssonIndices = append(validLesssonIndices, len(availableLessons)-1)
					teacherLessons[lesson.teacher.id] = append(teacherLessons[lesson.teacher.id], len(availableLessons)-1)
				}
			}

			for day, routine := range s.groups[groupIdx].routine {
				dayEntryIdx := classTimetables[classEntryIdx].findNode(day)
				startTime := routine.period.lowerMinuteCount

			dayGeneration:
				for startTime != routine.period.upperMinuteCount {
					if dayEntryIdx != -1 {
						startTime = classTimetables[classEntryIdx].days[dayEntryIdx].findNextTime(startTime)
						if startTime == routine.period.upperMinuteCount {
							break
						}
					}

					untriedLessonIndices := make([]int, len(validLesssonIndices)) // track indices of lessons that have not yet been tried
					copy(untriedLessonIndices, validLesssonIndices)

					for len(untriedLessonIndices) != 0 {
						currentLessonIdx := rand.Intn(len(untriedLessonIndices))
						currentTimeRange := timeRange{lowerMinuteCount: startTime, upperMinuteCount: startTime + s.groups[groupIdx].lessonDurationInMinutes}

						validRoutines := availableLessons[currentLessonIdx].teacher.routine[day]
						if len(validRoutines) != 0 {
							var valid bool
							for i := range validRoutines {
								if validRoutines[i].lowerMinuteCount <= currentTimeRange.lowerMinuteCount && validRoutines[i].upperMinuteCount >= currentTimeRange.upperMinuteCount {
									valid = true
									break
								}
							}
							if !valid {
								untriedLessonIndices = slices.DeleteFunc(untriedLessonIndices, func(a int) bool {
									return slices.Contains(teacherLessons[availableLessons[currentLessonIdx].teacher.id], a)
								})
								continue
							}
						}

						teacherEntryIdx, ok := teacherEntries[availableLessons[currentLessonIdx].teacher.id]
						if !ok {
							teacherTimetables = append(teacherTimetables, tTimetable{
								id:   availableLessons[currentLessonIdx].teacher.id,
								name: availableLessons[currentLessonIdx].teacher.name,
							})
							teacherEntryIdx = len(teacherTimetables) - 1
							teacherEntries[availableLessons[currentLessonIdx].teacher.id] = teacherEntryIdx
						}
						valid := teacherTimetables[teacherEntryIdx].insertNode(day, &tTimetableDayNode{
							subjectName:  availableLessons[currentLessonIdx].subject.name,
							subjectColor: availableLessons[currentLessonIdx].subject.color,
							className:    s.groups[groupIdx].classes[classIdx].name,
							period:       currentTimeRange,
						})
						if !valid {
							untriedLessonIndices = slices.DeleteFunc(untriedLessonIndices, func(a int) bool {
								return slices.Contains(teacherLessons[availableLessons[currentLessonIdx].teacher.id], a)
							})
							continue
						}

						availableLessons[currentLessonIdx].maxLessonCount--
						if availableLessons[currentLessonIdx].maxLessonCount <= 0 {
							validLesssonIndices = slices.DeleteFunc(validLesssonIndices, func(a int) bool {
								return a == currentLessonIdx
							})
						}
						classTimetables[classEntryIdx].insertNode(
							day, &cTimetableDayNode{
								period:       currentTimeRange,
								isLesson:     true,
								subjectName:  availableLessons[currentLessonIdx].subject.name,
								subjectColor: availableLessons[currentLessonIdx].subject.color,
								teacherName:  availableLessons[currentLessonIdx].teacher.name,
							},
						)
						continue dayGeneration
					}

					return false
				}
			}
		}
	}

	s.baseClassTimetables = classTimetables
	slices.SortFunc(s.baseClassTimetables, func(a, b cTimetable) int {
		return a.id - b.id
	})
	for i := range s.baseClassTimetables {
		s.baseClassTimetables[i].finalize()
	}
	s.baseTeacherTimetables = teacherTimetables
	slices.SortFunc(s.baseTeacherTimetables, func(a, b tTimetable) int {
		return a.id - b.id
	})
	for i := range s.baseTeacherTimetables {
		s.baseTeacherTimetables[i].finalize()
	}
	return true
}

// [CheckValidityOfClasses] and [CheckValidityOfSpecifics] must be called beforehand. Returns whether the process was successful or not
// Possible issues: strict teacher routines, restrictive maximum lesson count, few lesson options
func (s *school) GenerateTimetable() bool {
	if !s.areClassesValid {
		panic("all classes must be valid to proceed")
	}
	if !s.areSpecificsValid {
		panic("all mandatory lessons must be validated")
	}

	maxTries := 5
	for i := 0; i < maxTries; i++ {
		if s.generateTimetable() {
			s.areTimetablesGenerated = true
			break
		}
	}
	return s.areTimetablesGenerated
}

func addPdfFileToZip(zipWriter *zip.Writer, filepath string) error {
	file, err := os.Open(filepath)
	if err != nil {
		return fmt.Errorf("unable to open file, %w", err)
	}
	defer file.Close()

	info, err := file.Stat()
	if err != nil {
		return fmt.Errorf("unable to obtain file info, %w", err)
	}

	zipHeader, err := zip.FileInfoHeader(info)
	if err != nil {
		return fmt.Errorf("unable to create file header, %w", err)
	}
	zipHeader.Method = zip.Deflate

	writer, err := zipWriter.CreateHeader(zipHeader)
	if err != nil {
		return fmt.Errorf("unable to create zip writer for the file, %w", err)
	}

	_, err = io.Copy(writer, file)
	if err != nil {
		return fmt.Errorf("unable to write file to zip, %w", err)
	}
	return nil
}

// [GenerateTimetable] must be called beforehand.
// Returns the path of the created zip file or the first error encountered while perform I/O ops. It is the caller's responsibility to close and remove the zip file.
func (s *school) PrintTimetable() (zipFile *os.File, zipFileName string, errPrint error) {
	if !s.areTimetablesGenerated {
		panic("timetables must have been generated")
	}
	dir, err := os.MkdirTemp("", "timetables")
	if err != nil {
		return nil, "", fmt.Errorf("unable to make temporary directory, %w", err)
	}
	defer os.RemoveAll(dir)

	archive, err := os.CreateTemp("", "timetable*.zip")
	if err != nil {
		return nil, "", fmt.Errorf("unable to make zip file, %w", err)
	}
	defer func() {
		if errPrint != nil {
			_ = archive.Close()
			_ = os.Remove(archive.Name())
		}
	}()
	zipFileInfo, err := archive.Stat()
	if err != nil {
		return nil, "", fmt.Errorf("unable to obtain zip file info, %w", err)
	}

	zipWriter := zip.NewWriter(archive)
	defer zipWriter.Close()

	var g errgroup.Group
	for i := range s.baseClassTimetables {
		filepath := fmt.Sprintf("%v/class_%v.pdf", dir, s.baseClassTimetables[i].id)
		body := s.baseClassTimetables[i].htmlBody()
		g.Go(func() error {
			if err := generatePdf(filepath, body); err != nil {
				return fmt.Errorf("unable to generate class timetable, %w", err)
			}
			return addPdfFileToZip(zipWriter, filepath)
		})
	}
	for i := range s.baseTeacherTimetables {
		filepath := fmt.Sprintf("%v/teacher_%v.pdf", dir, s.baseTeacherTimetables[i].id)
		body := s.baseTeacherTimetables[i].htmlBody()
		g.Go(func() error {
			if err := generatePdf(filepath, body); err != nil {
				return fmt.Errorf("unable to generate teacher timetable, %w", err)
			}
			return addPdfFileToZip(zipWriter, filepath)
		})
	}
	if err := g.Wait(); err != nil {
		return nil, "", err
	}

	return archive, zipFileInfo.Name(), nil
}
