const SERVER_LIST = document.getElementById("server_list");
const RUNNING_SERVERS_TITLE = document.getElementById("running_servers_title");
const RUNNING_SERVERS_LIST = document.getElementById("running_servers_list");
const START_STOP_BUTTON = document.getElementById("start_stop_button");
const WELCOME_MESSAGE = document.getElementById("welcome_message");

const running_servers = [];

/**
 *
 * @param url String of URL to POST to.
 * @param data Data to POST. Optional.
 * @returns {Promise<(any | number)[]>} Response data and HTTP error code.
 */
async function post(url, data=null) {
    if (data === undefined || data === null) {
        data = {};
    }
    const resp = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    })
    const resp_data = await resp.json();
    return [resp_data, resp.status];
}

async function start_stop() {
    const name = SERVER_LIST.value;
    let action = "";
    if (running_servers.includes(name)) {
        action = "stop";
    } else {
        action = "start";
    }
    await post("/api/manage", {"name": name, "action": action});
    fetch_servers();
}

function login() {
    window.location.href = "/auth/authorize"
}

async function logout() {
    await post("/auth/logout");
    location.reload();
}

async function fetch_servers() {
    const resp = await post("/api/list");
    const old_selected = SERVER_LIST.value;
    SERVER_LIST.length = 0;
    if (resp[1] === 200) {
        const server_list = resp[0].data;
        let has_old_selected = false;
        running_servers.length = 0;
        for (const server of server_list) {
            const opt = document.createElement("option");
            opt.text = server.name;
            opt.value = server.name;
            if (server.running) {
                running_servers.push(server.name);
            }
            SERVER_LIST.add(opt);
            if (server.name === old_selected) {
                has_old_selected = true;
            }
        }
        if (has_old_selected) {
            SERVER_LIST.value = old_selected;
        }
        on_server_select_change();
        if (running_servers.length === 0) {
            RUNNING_SERVERS_TITLE.style.display = "none";
            RUNNING_SERVERS_LIST.style.display = "none";
        } else {
            RUNNING_SERVERS_LIST.innerHTML = "";
            for (const server of running_servers) {
                RUNNING_SERVERS_LIST.innerHTML += `<li>${server}</li>`;
            }
            RUNNING_SERVERS_TITLE.style.display = "block";
            RUNNING_SERVERS_LIST.style.display = "block";
        }

    } else {
        const opt = document.createElement("option");
        opt.text = "Error while retrieving servers!";
        SERVER_LIST.add(opt);
    }
}

function is_logged_in() {
    return WELCOME_MESSAGE !== null;
}

function on_server_select_change() {
    const name = SERVER_LIST.value;
    if (running_servers.includes(name)) {
        START_STOP_BUTTON.innerText = "Stop Server";
    } else {
        START_STOP_BUTTON.innerText = "Start Server";
    }
}

function init() {
    if (is_logged_in()) {
        fetch_servers();
        setInterval(fetch_servers, 4000);
    }
}


window.onload = () => init();