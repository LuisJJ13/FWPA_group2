// grab the calendar container from the page
const calendarContainer = document.getElementById('calendar-container');
// parse the medicine schedule data that was embedded in the html
const medicineSchedule = JSON.parse(calendarContainer.dataset.schedule);

const calendarGrid = document.getElementById('calendar-grid');
const monthDisplay = document.getElementById('calendar-month');

// keeps track of which month we're currently viewing
let currentDate = new Date();

function renderCalendar() {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    // show the current month and year at the top
    monthDisplay.textContent = currentDate.toLocaleString('default', { month: 'long', year: 'numeric' });

    // clear out the previous calendar before drawing the new one
    calendarGrid.innerHTML = '';

    // figure out what day of the week the month starts on
    const firstDay = new Date(year, month, 1).getDay();
    // and how many days are in this month
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    // add empty cells for the days before the month starts
    for (let i = 0; i < firstDay; i++) {
        const emptyCell = document.createElement('div');
        emptyCell.classList.add('calendar-cell', 'empty');
        calendarGrid.appendChild(emptyCell);
    }

    // create a cell for each day of the month
    for (let day = 1; day <= daysInMonth; day++) {
        const cell = document.createElement('div');
        cell.classList.add('calendar-cell');
        cell.textContent = day;

        // find all medicines scheduled for this specific day
        const dayMeds = medicineSchedule.filter(med => {
            const medDate = new Date(med.schedule_time);
            return medDate.getDate() === day && medDate.getMonth() === month && medDate.getFullYear() === year;
        });

        // if there are any meds scheduled, add them to the cell
        if (dayMeds.length > 0) {
            const list = document.createElement('ul');
            dayMeds.forEach(m => {
                const li = document.createElement('li');
                li.textContent = `${m.medication} @ ${new Date(m.schedule_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`;
                list.appendChild(li);
            });
            cell.appendChild(list);
        }

        calendarGrid.appendChild(cell);
    }
}

// go back one month when clicking the previous button
document.querySelector('.calendar-prev').addEventListener('click', () => {
    currentDate.setMonth(currentDate.getMonth() - 1);
    renderCalendar();
});

// go forward one month when clicking the next button
document.querySelector('.calendar-next').addEventListener('click', () => {
    currentDate.setMonth(currentDate.getMonth() + 1);
    renderCalendar();
});

// draw the calendar when the page first loads
renderCalendar();