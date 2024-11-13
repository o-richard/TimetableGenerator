package timetable

import (
	"math"
	"math/rand"
	"slices"
	"strconv"
	"strings"
	"unicode/utf8"
)

const (
	allowedColorCodeCharset = "ABCDEF0123456789"
)

func generateColorCode() string {
	var color strings.Builder
	color.WriteByte('#')
	for i := 0; i < 6; i++ {
		color.WriteByte(allowedColorCodeCharset[rand.Intn(len(allowedColorCodeCharset))])
	}
	return color.String()
}

func parseTimeRangeTime(s string) (mins uint, valid bool) {
	period := strings.SplitN(s, ":", 2)
	if len(period) != 2 {
		return
	}
	hour, err := strconv.ParseUint(period[0], 10, 0)
	if err != nil {
		return
	}
	minute, err := strconv.ParseUint(period[1], 10, 0)
	if err != nil {
		return
	}
	totalMinutes := ((hour % 24) * 60) + (minute % 60)
	return uint(totalMinutes), true
}

func parseTimeRange(s string) (detail timeRange, valid bool) {
	bounds := strings.SplitN(s, ",", 2)
	if len(bounds) != 2 {
		return
	}
	lowerBound, _ := strings.CutPrefix(bounds[0], "[")
	lower, ok := parseTimeRangeTime(lowerBound)
	if !ok {
		return
	}
	upperBound, _ := strings.CutSuffix(bounds[1], "]")
	upper, ok := parseTimeRangeTime(upperBound)
	if !ok {
		return
	}
	if upper <= lower {
		return
	}
	return timeRange{lowerMinuteCount: lower, upperMinuteCount: upper}, true
}

func overlapTimeTange(t1, t2 *timeRange) bool {
	return ((t1.lowerMinuteCount <= t2.lowerMinuteCount && t1.upperMinuteCount > t2.lowerMinuteCount) ||
		(t1.lowerMinuteCount >= t2.lowerMinuteCount && t1.lowerMinuteCount < t2.upperMinuteCount))
}

type VTeacher struct {
	Name    string            `json:"teacher_name"` // 1 - 30 characters
	Routine map[uint][]string `json:"routine"`      // optional mapping of day (1-Monday to 7-Sunday) to a list of time ranges (eg. '[9:00,11:00]'). non-overlapping.
}

func (t *VTeacher) validate() (detail teacher, valid bool) {
	t.Name = strings.TrimSpace(t.Name)
	if t.Name == "" || utf8.RuneCountInString(t.Name) > 30 {
		return
	}
	detail.name = t.Name

	if len(t.Routine) > 7 {
		return
	}
	detail.routine = make(map[day][]timeRange, len(t.Routine))
	for dayId, dayPeriods := range t.Routine {
		if dayId < 1 || dayId > 7 {
			return
		}

		specified := make([]timeRange, 0, len(dayPeriods))
		for i := range dayPeriods {
			timerange, ok := parseTimeRange(dayPeriods[i])
			if !ok {
				return
			}

			for i := range specified {
				if overlapTimeTange(&timerange, &specified[i]) {
					return
				}
			}
			specified = append(specified, timerange)
		}
		detail.routine[day(dayId)] = specified
	}

	return detail, true
}

type VGroupRoutine struct {
	Period string            `json:"period"` // time range (eg. '[9:00,11:00]')
	Breaks map[string]string `json:"breaks"` // optional mapping of break name (1 - 100 chracters) to time range (eg. '[9:00,11:00]'). within routine range & non-overlapping.
}

func (r *VGroupRoutine) validate() (detail groupRoutine, valid bool) {
	period, ok := parseTimeRange(r.Period)
	if !ok {
		return
	}
	detail.period = period

	detail.breaks = make([]groupRoutineBreak, 0, len(r.Breaks))
	specified := make([]timeRange, 0, len(r.Breaks))
	for breakName, breakPeriod := range r.Breaks {
		breakName = strings.TrimSpace(breakName)
		if breakName == "" || utf8.RuneCountInString(breakName) > 100 {
			return
		}

		breakTimeRange, ok := parseTimeRange(breakPeriod)
		if !ok {
			return
		}

		if breakTimeRange.lowerMinuteCount < period.lowerMinuteCount || breakTimeRange.upperMinuteCount > period.upperMinuteCount {
			return
		}
		for i := range specified {
			if overlapTimeTange(&breakTimeRange, &specified[i]) {
				return
			}
		}

		detail.breaks = append(detail.breaks, groupRoutineBreak{name: breakName, period: breakTimeRange})
		specified = append(specified, breakTimeRange)
	}
	slices.SortFunc(detail.breaks, func(a, b groupRoutineBreak) int {
		return int(a.period.lowerMinuteCount - b.period.lowerMinuteCount)
	})

	return detail, true
}

type VGroupClassLesson struct {
	SubjectId      int    `json:"subject_id"`       // pre-specified subject id
	TeacherId      int    `json:"teacher_id"`       // pre-specified teacher id
	MaxLessonCount uint32 `json:"max_lesson_count"` // optional maximum number of lessons in a week including the total count of mandatory specifics (specified duration is unconsidered).

	MandatorySpecifics map[uint][]string `json:"mandatory_specifics"` // optional mapping of day (1-Monday to 7-Sunday) to a list of time ranges (eg. '[9:00,11:00]'). within routine range & non-overlapping.
}

func (l *VGroupClassLesson) validate(subjects map[int]*subject, teachers map[int]*teacher) (detail groupClassLesson, valid bool) {
	subject, ok := subjects[l.TeacherId]
	if !ok {
		return
	}
	detail.subject = subject

	teacher, ok := teachers[l.TeacherId]
	if !ok {
		return
	}
	detail.teacher = teacher

	if len(l.MandatorySpecifics) > 7 {
		return
	}
	var mandatorySpecificsCount int
	detail.mandatorySpecifics = make(map[day][]timeRange, len(l.MandatorySpecifics))
	for dayId, dayPeriods := range l.MandatorySpecifics {
		if dayId < 1 || dayId > 7 {
			return
		}

		periods := make([]timeRange, 0, len(dayPeriods))
		for i := range dayPeriods {
			timerange, ok := parseTimeRange(dayPeriods[i])
			if !ok {
				return
			}
			periods = append(periods, timerange)
		}
		mandatorySpecificsCount += len(periods)
		detail.mandatorySpecifics[day(dayId)] = periods
	}

	if l.MaxLessonCount == 0 {
		detail.maxLessonCount = math.MaxInt
	} else {
		detail.maxLessonCount = int(l.MaxLessonCount)
	}
	detail.maxLessonCount -= mandatorySpecificsCount
	return detail, true
}

type VGroupClass struct {
	Name      string              `json:"class_name"`           // 1 - 100 characters
	TeacherId int                 `json:"teacher_in_charge_id"` // pre-specified teacher id
	Lessons   []VGroupClassLesson `json:"lessons"`              // required
}

func (c *VGroupClass) validate(subjects map[int]*subject, teachers map[int]*teacher, routine map[day]groupRoutine) (detail groupClass, valid bool) {
	c.Name = strings.TrimSpace(c.Name)
	if c.Name == "" || utf8.RuneCountInString(c.Name) > 100 {
		return
	}
	detail.name = c.Name

	headTeacher, ok := teachers[c.TeacherId]
	if !ok {
		return
	}
	detail.teacher = headTeacher

	if len(c.Lessons) == 0 {
		return
	}
	detail.lessons = make([]groupClassLesson, 0, len(c.Lessons))
	for i := range c.Lessons {
		lesson, ok := c.Lessons[i].validate(subjects, teachers)
		if !ok {
			return
		}
		detail.lessons = append(detail.lessons, lesson)
	}

	specified := make(map[day][]timeRange, len(routine))
	for day := range routine {
		specified[day] = make([]timeRange, 0, len(routine[day].breaks))
		for _, breakPeriod := range routine[day].breaks {
			specified[day] = append(specified[day], breakPeriod.period)
		}
	}
	detail.specifics = make(map[day][]groupClassLessonSpecifics)
	for i := range detail.lessons {
		for day, periods := range detail.lessons[i].mandatorySpecifics {
			for _, t1 := range periods {
				if t1.lowerMinuteCount < routine[day].period.lowerMinuteCount || t1.upperMinuteCount > routine[day].period.upperMinuteCount {
					return
				}
				for _, t2 := range specified[day] {
					if overlapTimeTange(&t1, &t2) {
						return
					}
				}
				specified[day] = append(specified[day], t1)
				detail.specifics[day] = append(detail.specifics[day], groupClassLessonSpecifics{subject: detail.lessons[i].subject, teacher: detail.lessons[i].teacher, period: t1})
			}
		}
	}
	for day := range detail.specifics {
		slices.SortFunc(detail.specifics[day], func(a, b groupClassLessonSpecifics) int {
			return int(a.period.lowerMinuteCount - b.period.lowerMinuteCount)
		})
	}

	return detail, true
}

type VGroup struct {
	Name    string                 `json:"group_name"` // 1 - 500 characters
	Routine map[uint]VGroupRoutine `json:"routine"`    // required mapping of day (1-Monday to 7-Sunday) to routine
	Classes []VGroupClass          `json:"classes"`    // required

	LessonDurationInMinutes uint `json:"lesson_duration_in_minutes"` // minimum of 1
}

func (g *VGroup) validate(subjects map[int]*subject, teachers map[int]*teacher) (detail group, valid bool) {
	if g.LessonDurationInMinutes < 1 {
		return
	}
	detail.lessonDurationInMinutes = g.LessonDurationInMinutes

	g.Name = strings.TrimSpace(g.Name)
	if g.Name == "" || utf8.RuneCountInString(g.Name) > 500 {
		return
	}
	detail.name = g.Name

	if len(g.Routine) == 0 || len(g.Routine) > 7 {
		return
	}
	detail.routine = make(map[day]groupRoutine, len(g.Routine))
	for dayId, dayRoutine := range g.Routine {
		if dayId < 1 || dayId > 7 {
			return
		}
		routine, ok := dayRoutine.validate()
		if !ok {
			return
		}
		detail.routine[day(dayId)] = routine
	}

	if len(g.Classes) == 0 {
		return
	}
	detail.classes = make([]groupClass, 0, len(g.Classes))
	for i := range g.Classes {
		class, ok := g.Classes[i].validate(subjects, teachers, detail.routine)
		if !ok {
			return
		}
		detail.classes = append(detail.classes, class)
	}

	return detail, true
}

type VSchool struct {
	Subjects map[int]string   `json:"subjects"` // required mapping of an id to subject name (1 - 30 characters).
	Teachers map[int]VTeacher `json:"teachers"` // required mapping of an id to teacher.
	Groups   []VGroup         `json:"groups"`   // required
}

func (s *VSchool) Validate() (*school, bool) {
	if len(s.Subjects) == 0 {
		return nil, false
	}
	subjects := make(map[int]*subject, len(s.Subjects))
	for id, subjectName := range s.Subjects {
		subjectName = strings.TrimSpace(subjectName)
		if subjectName == "" || utf8.RuneCountInString(subjectName) > 30 {
			return nil, false
		}
		subjects[id] = &subject{name: subjectName, color: generateColorCode()}
	}

	if len(s.Teachers) == 0 {
		return nil, false
	}
	teachers := make(map[int]*teacher, len(s.Teachers))
	for id, v := range s.Teachers {
		teacher, ok := v.validate()
		if !ok {
			return nil, false
		}
		teacher.id = id
		teachers[id] = &teacher
	}

	if len(s.Groups) == 0 {
		return nil, false
	}
	school := school{groups: make([]group, 0, len(s.Groups))}
	for i := range s.Groups {
		group, ok := s.Groups[i].validate(subjects, teachers)
		if !ok {
			return nil, false
		}
		school.groups = append(school.groups, group)
	}

	return &school, true
}
