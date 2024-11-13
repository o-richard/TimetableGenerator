package timetable

import (
	"fmt"
	"slices"
	"strings"
)

type cTimetableDayNode struct {
	period                                 timeRange
	isLesson                               bool // whether the node is a lesson or break
	breakName                              string
	subjectName, subjectColor, teacherName string
}

type cTimetableDay struct {
	day   day
	nodes []cTimetableDayNode // ordered by time range in an ascending order
}

func (d *cTimetableDay) findNextTime(startTime uint) uint {
	for i := range d.nodes {
		if d.nodes[i].period.lowerMinuteCount == startTime {
			startTime = d.nodes[i].period.upperMinuteCount
		}
		if d.nodes[i].period.lowerMinuteCount > startTime {
			break
		}
	}
	return startTime
}

type cTimetable struct {
	id               int
	groupName        string
	className        string
	classTeacherName string
	checkpoints      []uint          //  list of possible start times & end times of lessons/breaks ordered in an ascending order. distinct elements in an ascending order.
	days             []cTimetableDay // ordered by day in an ascending order
}

func (t *cTimetable) copy() cTimetable {
	cpy := cTimetable{id: t.id, groupName: t.groupName, className: t.className, classTeacherName: t.classTeacherName, days: make([]cTimetableDay, 0, len(t.days))}
	for dayIdx := range t.days {
		nodes := make([]cTimetableDayNode, 0, len(t.days[dayIdx].nodes))
		nodes = append(nodes, t.days[dayIdx].nodes...)
		cpy.days = append(cpy.days, cTimetableDay{day: t.days[dayIdx].day, nodes: nodes})
	}
	return cpy
}

func (t *cTimetable) findNode(day day) int {
	dayIndex := -1
	for i := range t.days {
		if t.days[i].day == day {
			return i
		}
	}
	return dayIndex
}

func (t *cTimetable) insertNode(day day, node *cTimetableDayNode) {
	dayIndex := t.findNode(day)
	if dayIndex == -1 {
		t.days = append(t.days, cTimetableDay{day: day, nodes: []cTimetableDayNode{*node}})
		return
	}

	t.days[dayIndex].nodes = append(t.days[dayIndex].nodes, *node)
	slices.SortFunc(t.days[dayIndex].nodes, func(a, b cTimetableDayNode) int {
		return int(a.period.lowerMinuteCount - b.period.lowerMinuteCount)
	})
}

func (t *cTimetable) finalize() {
	slices.SortFunc(t.days, func(a, b cTimetableDay) int {
		return int(a.day - b.day)
	})
	t.checkpoints = nil
	for dayIdx := range t.days {
		for nodeIdx := range t.days[dayIdx].nodes {
			if !slices.Contains(t.checkpoints, t.days[dayIdx].nodes[nodeIdx].period.lowerMinuteCount) {
				t.checkpoints = append(t.checkpoints, t.days[dayIdx].nodes[nodeIdx].period.lowerMinuteCount)
			}
			if !slices.Contains(t.checkpoints, t.days[dayIdx].nodes[nodeIdx].period.upperMinuteCount) {
				t.checkpoints = append(t.checkpoints, t.days[dayIdx].nodes[nodeIdx].period.upperMinuteCount)
			}
		}
	}
	slices.Sort(t.checkpoints)
}

// must be called after .finalize()
func (t *cTimetable) htmlBody() string {
	var body strings.Builder
	_, _ = body.WriteString(`<div><h1 style="text-align: center; font-weight: 900; font-size: 20px;">Class: `)
	_, _ = body.WriteString(t.className)
	_, _ = body.WriteString(`</h1><h1 style="text-align: center; font-weight: 900; font-size: 20px;">Class Teacher: `)
	_, _ = body.WriteString(t.classTeacherName)
	_, _ = body.WriteString("</h1></div><table><tr><th>Day</th>")

	for i := range t.checkpoints {
		if i+1 == len(t.checkpoints) {
			break
		}
		_, _ = body.WriteString(fmt.Sprintf("<th>%02d:%02d - %02d:%02d</th>", t.checkpoints[i]/60, t.checkpoints[i]%60, t.checkpoints[i+1]/60, t.checkpoints[i+1]%60))
	}
	_, _ = body.WriteString("</tr>")

	for dayIdx := range t.days {
		_, _ = body.WriteString("<tr><td>")
		_, _ = body.WriteString(dayName(t.days[dayIdx].day))
		_, _ = body.WriteString("</td>")

		start := t.checkpoints[0]
		for _, node := range t.days[dayIdx].nodes {
			if node.period.lowerMinuteCount > start {
				colspan := slices.Index(t.checkpoints, node.period.lowerMinuteCount) - slices.Index(t.checkpoints, start)
				_, _ = body.WriteString(fmt.Sprintf(`<td colspan="%d"></td>`, colspan))
			}

			colspan := slices.Index(t.checkpoints, node.period.upperMinuteCount) - slices.Index(t.checkpoints, node.period.lowerMinuteCount)
			if node.isLesson {
				_, _ = body.WriteString(fmt.Sprintf(`<td colspan="%d" style="background-color: %v67;"><p>%v</p><p>%v</p></td>`, colspan, node.subjectColor, node.subjectName, node.teacherName))
			} else {
				_, _ = body.WriteString(fmt.Sprintf(`<td colspan="%d">%v</td>`, colspan, node.breakName))
			}
			start = node.period.upperMinuteCount
		}
		if start != t.checkpoints[len(t.checkpoints)-1] {
			colspan := slices.Index(t.checkpoints, t.checkpoints[len(t.checkpoints)-1]) - slices.Index(t.checkpoints, start)
			_, _ = body.WriteString(fmt.Sprintf(`<td colspan="%d"></td>`, colspan))
		}

		_, _ = body.WriteString("</tr>")
	}
	_, _ = body.WriteString("</table>")

	return body.String()
}

type tTimetableDayNode struct {
	subjectName, subjectColor, className string
	period                               timeRange
}

type tTimetableDay struct {
	day   day
	nodes []tTimetableDayNode // ordered by time range in an ascending order
}

type tTimetable struct {
	id          int
	name        string
	days        []tTimetableDay // ordered by day in an ascending order
	checkpoints []uint          //  list of possible start times & end times of lessons ordered in an ascending order. distinct elements in an ascending order.
}

func (t *tTimetable) copy() tTimetable {
	cpy := tTimetable{id: t.id, name: t.name, days: make([]tTimetableDay, 0, len(t.days))}
	for dayIdx := range t.days {
		nodes := make([]tTimetableDayNode, 0, len(t.days[dayIdx].nodes))
		nodes = append(nodes, t.days[dayIdx].nodes...)
		cpy.days = append(cpy.days, tTimetableDay{day: t.days[dayIdx].day, nodes: nodes})
	}
	return cpy
}

func (t *tTimetable) findNode(day day) int {
	dayIndex := -1
	for i := range t.days {
		if t.days[i].day == day {
			return i
		}
	}
	return dayIndex
}

func (t *tTimetable) insertNode(day day, node *tTimetableDayNode) (valid bool) {
	dayIndex := t.findNode(day)
	if dayIndex == -1 {
		t.days = append(t.days, tTimetableDay{day: day, nodes: []tTimetableDayNode{*node}})
		return true
	}

	for i := range t.days[dayIndex].nodes {
		if overlapTimeTange(&t.days[dayIndex].nodes[i].period, &node.period) {
			return false
		}
	}
	t.days[dayIndex].nodes = append(t.days[dayIndex].nodes, *node)
	slices.SortFunc(t.days[dayIndex].nodes, func(a, b tTimetableDayNode) int {
		return int(a.period.lowerMinuteCount - b.period.lowerMinuteCount)
	})

	return true
}

func (t *tTimetable) finalize() {
	slices.SortFunc(t.days, func(a, b tTimetableDay) int {
		return int(a.day - b.day)
	})
	t.checkpoints = nil
	for dayIdx := range t.days {
		for nodeIdx := range t.days[dayIdx].nodes {
			if !slices.Contains(t.checkpoints, t.days[dayIdx].nodes[nodeIdx].period.lowerMinuteCount) {
				t.checkpoints = append(t.checkpoints, t.days[dayIdx].nodes[nodeIdx].period.lowerMinuteCount)
			}
			if !slices.Contains(t.checkpoints, t.days[dayIdx].nodes[nodeIdx].period.upperMinuteCount) {
				t.checkpoints = append(t.checkpoints, t.days[dayIdx].nodes[nodeIdx].period.upperMinuteCount)
			}
		}
	}
	slices.Sort(t.checkpoints)
}

// must be called after .finalize()
func (t *tTimetable) htmlBody() string {
	var body strings.Builder
	_, _ = body.WriteString(`<div><h1 style="text-align: center; font-weight: 900; font-size: 20px;">Teacher: `)
	_, _ = body.WriteString(t.name)
	_, _ = body.WriteString("</h1></div><table><tr><th>Day</th>")

	for i := range t.checkpoints {
		if i+1 == len(t.checkpoints) {
			break
		}
		_, _ = body.WriteString(fmt.Sprintf("<th>%02d:%02d - %02d:%02d</th>", t.checkpoints[i]/60, t.checkpoints[i]%60, t.checkpoints[i+1]/60, t.checkpoints[i+1]%60))
	}
	_, _ = body.WriteString("</tr>")

	for dayIdx := range t.days {
		_, _ = body.WriteString("<tr><td>")
		_, _ = body.WriteString(dayName(t.days[dayIdx].day))
		_, _ = body.WriteString("</td>")

		start := t.checkpoints[0]
		for _, node := range t.days[dayIdx].nodes {
			if node.period.lowerMinuteCount > start {
				colspan := slices.Index(t.checkpoints, node.period.lowerMinuteCount) - slices.Index(t.checkpoints, start)
				_, _ = body.WriteString(fmt.Sprintf(`<td colspan="%d"></td>`, colspan))
			}

			colspan := slices.Index(t.checkpoints, node.period.upperMinuteCount) - slices.Index(t.checkpoints, node.period.lowerMinuteCount)
			_, _ = body.WriteString(fmt.Sprintf(`<td colspan="%d" style="background-color: %v67;"><p>%v</p><p>%v</p></td>`, colspan, node.subjectColor, node.subjectName, node.className))
			start = node.period.upperMinuteCount
		}
		if start != t.checkpoints[len(t.checkpoints)-1] {
			colspan := slices.Index(t.checkpoints, t.checkpoints[len(t.checkpoints)-1]) - slices.Index(t.checkpoints, start)
			_, _ = body.WriteString(fmt.Sprintf(`<td colspan="%d"></td>`, colspan))
		}

		_, _ = body.WriteString("</tr>")
	}
	_, _ = body.WriteString("</table>")

	return body.String()
}
