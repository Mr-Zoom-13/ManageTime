const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';

async function postJson(url, body) {
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json;charset=utf-8',
            'Accept': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(body)
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(payload.error || 'Запрос не выполнен.');
    }
    return payload;
}

function taskPayload(button) {
    return {
        user_id: Number(button.dataset.user),
        project_id: Number(button.dataset.project),
        task_id: Number(button.dataset.task)
    };
}

async function delete_project(button) {
    if (!confirm('Удалить проект вместе со всеми задачами?')) return;
    try {
        await postJson('/api/delete-project', {
            user_id: Number(button.dataset.user),
            project_id: Number(button.dataset.project)
        });
        button.closest('tr').remove();
    } catch (error) {
        alert(error.message);
    }
}

async function delete_task(button) {
    if (!confirm('Удалить задачу?')) return;
    try {
        await postJson('/api/delete-task', taskPayload(button));
        button.closest('tr').remove();
    } catch (error) {
        alert(error.message);
    }
}

function setTimerState(button, running) {
    const {user, project, task} = button.dataset;
    document.getElementById(`start-${user}-${project}-${task}`).style.display = running ? 'none' : '';
    document.getElementById(`stop-${user}-${project}-${task}`).style.display = running ? '' : 'none';
    button.closest('tr').style.backgroundColor = running ? 'greenyellow' : 'transparent';
}

async function start(button) {
    try {
        await postJson('/api/start-stopwatch', taskPayload(button));
        setTimerState(button, true);
    } catch (error) {
        alert(error.message);
    }
}

async function stop(button) {
    try {
        const result = await postJson('/api/stop-stopwatch', taskPayload(button));
        setTimerState(button, false);
        const {user, project, task} = button.dataset;
        document.getElementById(`duration-${user}-${project}-${task}`).textContent =
            `Дни: ${result.days}; часы: ${result.hours}; минуты: ${result.minutes}`;
    } catch (error) {
        alert(error.message);
    }
}

async function reset(button) {
    if (!confirm('Сбросить накопленное время?')) return;
    try {
        await postJson('/api/reset-stopwatch', taskPayload(button));
        setTimerState(button, false);
        const {user, project, task} = button.dataset;
        document.getElementById(`duration-${user}-${project}-${task}`).textContent =
            'Дни: 0; часы: 0; минуты: 0';
    } catch (error) {
        alert(error.message);
    }
}

function tableSearch() {
    const query = document.getElementById('search-text').value.trim().toLowerCase();
    const rows = document.querySelectorAll('#info-table tr:not(:first-child)');
    rows.forEach((row) => {
        row.style.display = row.textContent.toLowerCase().includes(query) ? '' : 'none';
    });
}
