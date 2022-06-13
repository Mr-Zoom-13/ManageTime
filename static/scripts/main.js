function delete_project(this_) {
    user = $(this_).data('user')
    project = $(this_).data('project')
    document.getElementById(String(user) + " " + String(project)).remove()
    fetch('/api/delete-project', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json;charset=utf-8',
            'Accept': 'application/json'
        },
        body: JSON.stringify({"user_id": user, "project_id": project})
    })
        .then((response) => {
            return response.json();
        })
        .then((myjson) => {
        });
}

function delete_task(this_) {
    user = $(this_).data('user')
    project = $(this_).data('project')
    task = $(this_).data('task')
    document.getElementById(String(user) + "-" + String(project) + "-" + String(task)).remove()
    fetch('/api/delete-task', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json;charset=utf-8',
            'Accept': 'application/json'
        },
        body: JSON.stringify({"user_id": user, "project_id": project, "task_id": task})
    })
        .then((response) => {
            return response.json();
        })
        .then((myjson) => {
        });
}

function start(this_) {
    user = $(this_).data('user')
    project = $(this_).data('project')
    task = $(this_).data('task')
    $(this_).fadeToggle(1)
    my_tr = $("#" + String(user) + "-" + String(project) + "-" + String(task))
    my_tr.css('background-color', ' greenyellow')
    $('#stop-' + String(user) + "-" + String(project) + "-" + String(task)).fadeToggle(1)
    fetch('/api/start-stopwatch', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json;charset=utf-8',
            'Accept': 'application/json'
        },
        body: JSON.stringify({"user_id": user, "project_id": project, "task_id": task})
    })
        .then((response) => {
            return response.json();
        })
        .then((myjson) => {
        });
}

function stop(this_) {
    user = $(this_).data('user')
    project = $(this_).data('project')
    task = $(this_).data('task')
    $(this_).fadeToggle(1)
    $('#start-' + String(user) + "-" + String(project) + "-" + String(task)).fadeToggle(1)
    my_tr = $("#" + String(user) + "-" + String(project) + "-" + String(task))
    my_tr.css('background-color', 'transparent')
    fetch('/api/stop-stopwatch', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json;charset=utf-8',
            'Accept': 'application/json'
        },
        body: JSON.stringify({"user_id": user, "project_id": project, "task_id": task})
    })
        .then((response) => {
            return response.json();
        })
        .then((myjson) => {
            $('#duration-' + String(user) + "-" + String(project) + "-" + String(task)).html('Duration: Days: ' + String(myjson.days) + '; Hours: ' + String(myjson.hours) + '; Minutes: ' + String(myjson.minutes) + ";")
        });
}

function reset(this_) {
    if (confirm("Are you sure you want to reset the time?")) {
        user = $(this_).data('user')
        project = $(this_).data('project')
        task = $(this_).data('task')
        obj1 = document.getElementById('start-' + String(user) + "-" + String(project) + "-" + String(task));
        if (window.getComputedStyle(obj1, null).getPropertyValue("display") == 'none') {
            $('#start-' + String(user) + "-" + String(project) + "-" + String(task)).fadeToggle(1)
            $('#stop-' + String(user) + "-" + String(project) + "-" + String(task)).fadeToggle(1)
            my_tr = $("#" + String(user) + "-" + String(project) + "-" + String(task))
            my_tr.css('background-color', 'transparent')
        }
        $('#duration-' + String(user) + "-" + String(project) + "-" + String(task)).html('Duration: Days: 0; Hours: 0; Minutes: 0;')
        fetch('/api/reset-stopwatch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json;charset=utf-8',
                'Accept': 'application/json'
            },
            body: JSON.stringify({"user_id": user, "project_id": project, "task_id": task})
        })
            .then((response) => {
                return response.json();
            })
            .then((myjson) => {
            });
    }

}