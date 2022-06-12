function delete_project (this_) {
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

function delete_task (this_) {
  user = $(this_).data('user')
  project = $(this_).data('project')
  task = $(this_).data('task')
  document.getElementById(String(user) + " " + String(project) + " " + String(task)).remove()
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