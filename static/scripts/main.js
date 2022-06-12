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
      body: JSON.stringify({"user_id": $(this_).data('user'), "project_id": $(this_).data('project')})
    })
            .then((response) => {
                return response.json();
            })
            .then((myjson) => {
            });
}