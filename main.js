const coursePickerForm = document.querySelector("#course-picker").querySelector("form");
const semesterInput    = document.querySelector("#semester");
const courseInput      = document.querySelector("#course-id");

let ucIdMap    = new Map(); // Maps pv_ocorrencia_id to ucs
let ucYearMap  = new Map(); // Maps curricular year to ucs
let checkedUcs = new Set();

const ucPickerDiv  = document.querySelector("#uc-picker");
const ucOptionsDiv = document.querySelector("#uc-options");
const ucPickerForm = ucPickerDiv.querySelector("form");

const examsDiv         = document.querySelector("#exams");
const examsTableHeader = document.querySelector("#exams-header"); 
const examsTableData   = document.querySelector("#exams-data");

/** 
 * Loads a JSON file and executes a callback on it
 * @param {string}   jsonPath The path to the JSON file
 * @param {Function} callback  The callback function that receives the the JSON object as an argument
*/
function loadJson(jsonPath, callback) {
    let xhttp = new XMLHttpRequest();
    let response;
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            response = JSON.parse(xhttp.responseText);
            callback(response);
        }
    }
    xhttp.open("GET", jsonPath, true);
    xhttp.send();
}

/**
 * Compares two items by acronym
 * @param {JSON} item1 
 * @param {JSON} item2 
 */
function compareAcronyms(item1, item2) {
    if (item1.acronym < item2.acronym) {
        return -1;
    } else if (item1.acronym === item2.acronym) {
        return 0;
    } else {
        return 1;
    }
}

/**
 * Returns the day of the week from a date
 * @param {Date} date A Date object 
 * @return {string} The day of the week (Monday, Tuesday, etc.)
 * https://stackoverflow.com/a/45464959
 */
function getWeekday(date) {
    return date.toLocaleDateString("en-US", { weekday: 'long' });        
}


function loadCoursesOptions(json) {
    json.sort(compareAcronyms);
    let output = '';
    for(let course of json) {
        output += `<option value="${course.course_id}">${course.acronym}</option>`;
    }
    courseInput.innerHTML = output;
}
loadJson("data/courses.json", loadCoursesOptions);

function onCourseSubmit(e) {
    e.preventDefault();
    examsDiv.style.display = "none";
    let uc_path = `data/courses/COURSE${courseInput.value}/SEMESTER${semesterInput.value}.json`;
    ucPickerDiv.style.display = "block";
    loadJson(uc_path, loadCurricularUnits);
}
coursePickerForm.addEventListener("submit", onCourseSubmit);

function loadCurricularUnits(json) {
    ucIdMap.clear();
    for(let uc of json) {
        ucIdMap.set(uc.pv_ocorrencia_id, uc);
    }

    ucYearMap.clear();

    // I'm presetting the keys of the map so that they are ordered
    // The correct way to do this would be to use a set or to reorder the keys of the map
    // Or even better, use an orderedMap (which doesn't exist in vanilla JS IIRC :( )
    // Either way, I'd like to apologize for this little hack
    for (let i = 1; i < 11; i++) {
        ucYearMap.set(i, []);
    }

    for(let uc of json) {
        ucYearMap.get(uc.curricular_year).push(uc);
    }

    // Deleting empty keys
    for (let i = 1; i < 11; i++) {
        if (ucYearMap.get(i).length === 0) {
            ucYearMap.delete(i);
        }
    }

    let output = '';
    for (let [curricular_year, ucs] of ucYearMap) {
        let ucs_checkboxes = '';
        for (let uc of ucs) {
            ucs_checkboxes +=
            `<div class = "uc-option">
                 <input type="checkbox" id="${uc.pv_ocorrencia_id}" class="normal-checkbox" value="${uc.pv_ocorrencia_id}">
                 <label for="${uc.pv_ocorrencia_id}">${uc.acronym}</label>
             </div>`;
        }
        output += 
        `<div class = "uc-box">
            <div class = "uc-option">
                <input type="checkbox" id="master${curricular_year}" class = "master-checkbox" value = "${curricular_year}">
                <label for="master${curricular_year}"><h3>Year ${curricular_year}</h3></label>
            </div>
             ${ucs_checkboxes}
         </div>`
    }

    ucOptionsDiv.innerHTML = output;


    //Wiring all the checkboxes
    for (let checkbox of ucPickerForm.querySelectorAll(".master-checkbox")) {
        checkbox.addEventListener("click", onMasterCheckboxCLick);
    }

    for (let checkbox of ucPickerForm.querySelectorAll(".normal-checkbox")) {
        checkbox.addEventListener("click", onNormalCheckboxCLick);
    }
}

function onMasterCheckboxCLick(e) {
    let idString = `#master${e.target.value}`;

    ucBox = ucPickerForm.querySelector(idString).parentNode.parentNode;

    for (let input of ucBox.querySelectorAll("input")) {
        input.checked = e.target.checked;
    }
}

function onNormalCheckboxCLick(e) {
    let curricular_year = ucIdMap.get(Number(e.target.value)).curricular_year;
    let idString = `#master${curricular_year}`;

    masterCheckbox = ucPickerForm.querySelector(idString);
    ucBox = masterCheckbox.parentNode.parentNode;

    let nChecked = 0;
    let nUnchecked = 0;
    
    for (let input of ucBox.querySelectorAll("input")) {
        if (!isNaN(input.id)) {
            if (input.checked) {
                nChecked++;
            } else {
                nUnchecked++;
            }

            if ((nChecked > 0) && (nUnchecked > 0)) {
                masterCheckbox.indeterminate = true;
                return;
            }
        }
    }

    if (nChecked == 0) {
        masterCheckbox.checked = false;
    } else {
        masterCheckbox.checked = true;
    }
}

function onUcSubmit(e) {
    e.preventDefault();

    checkedUcs.clear()
    for (let checkbox of ucPickerForm.querySelectorAll(".normal-checkbox")) {
        if (checkbox.checked) {
            checkedUcs.add(Number(checkbox.value));
        }
    }

    let uc_path = `data/courses/COURSE${courseInput.value}/EXAMS.json`;
    examsDiv.style.display = "block";
    loadJson(uc_path, loadExams);
}
ucPickerForm.addEventListener("submit", onUcSubmit);

function loadExams(json) {
    json.sort((item1, item2) => item1.start_timestamp - item2.start_timestamp);

    let output = '';
    for (let exam of json) {
        if (checkedUcs.has(exam.pv_ocorrencia_id)) {
            let acronym = ucIdMap.get(exam.pv_ocorrencia_id).acronym;

            let start   = new Date(exam.start_timestamp  * 1000);
            let finish  = new Date(exam.finish_timestamp * 1000);
            
            let weekday    = getWeekday(start);
            let day        = start .toISOString().slice(-24, -14);

            let startHour  = start .toISOString().slice(-13, -8); //https://stackoverflow.com/a/35890537
            let finishHour = finish.toISOString().slice(-13, -8);

            let rooms      = exam.rooms.join(" ");
            
            output +=
            `<tr>
                <td>${acronym}</td>
                <td>${day}</td>
                <td>${weekday}</td>
                <td>${startHour}</td>
                <td>${finishHour}</td>
                <td>${rooms}</td>
             </tr>`;
        }
    }

    examsTableData.innerHTML = output;
}