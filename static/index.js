const SERVER_LIST = document.getElementById("server_list");
const RUNNING_SERVERS_TITLE = document.getElementById("running_servers_title");
const RUNNING_SERVERS_LIST = document.getElementById("running_servers_list");
const START_STOP_BUTTON = document.getElementById("start_stop_button");
const WELCOME_MESSAGE = document.getElementById("welcome_message");
const STATUS = document.getElementById("status");
const BACKGROUND_STATUS = document.getElementById("background_status");
const SERVER_DATA = document.getElementById("server_data");
const SERVER_DATA_TITLE = document.getElementById("server_data_title");
const SERVER_DATA_LOG = document.getElementById("server_data_log");

const running_servers = [];
let selected_server = null;

/**
 *
 * @param url String of URL to POST to.
 * @param data Data to POST. Optional.
 * @param show_alert Whether the response should show an alert.
 * @returns {Promise<(any | number)[]>} Response data and HTTP error code.
 */
async function post(url, data=null, show_alert=true) {
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
    if (show_alert) {
        window.alert(resp_data.message);
    }
    return [resp_data, resp.status];
}

async function start_stop() {
    const name = SERVER_LIST.value;
    let action = "";
    if (is_server_running(name)) {
        action = "stop";
        set_status(`Stopping server ${name}`);
    } else {
        action = "start";
        set_status(`Starting server ${name}`);
    }
    await post("/api/manage", {"name": name, "action": action});
    set_status(null);
    await fetch_servers();
    show_server_details(name);
}

function login() {
    window.location.href = "/auth/authorize"
}

async function logout() {
    set_status("Logging out...");
    await post("/auth/logout");
    location.reload();
}

async function fetch_servers() {
    set_status("Fetching server list", true);
    const resp = await post("/api/list", null, false);
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
                running_servers.push(server);
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
                RUNNING_SERVERS_LIST.innerHTML += `<li><a href="javascript:show_server_details('${server.name}')">${server.name}</a></li>`;
            }
            RUNNING_SERVERS_TITLE.style.display = "block";
            RUNNING_SERVERS_LIST.style.display = "block";
        }
    } else {
        const opt = document.createElement("option");
        opt.text = "Error while retrieving servers!";
        SERVER_LIST.add(opt);
    }
    set_status(null, true);
    update_server_data();
}

function is_logged_in() {
    return WELCOME_MESSAGE !== null;
}

function on_server_select_change() {
    const name = SERVER_LIST.value;
    let server_running = is_server_running(name);
    if (server_running) {
        START_STOP_BUTTON.innerText = "Stop Server";
    } else {
        START_STOP_BUTTON.innerText = "Start Server";
    }
}

function set_status(msg, is_background=false) {
    const elem = is_background ? BACKGROUND_STATUS : STATUS;
    const start_text = is_background ? "Background Status: " : "Status: ";
    if (msg === null || msg === undefined) {
        msg = is_background ? "Performing no background tasks..." : "Waiting to do something...";
    }
    elem.innerText = start_text + msg;
}

function show_server_details(server_name) {
    selected_server = server_name;
    update_server_data();
}

function update_server_data() {
    let server_data = get_running_server(selected_server);
    if (server_data === null) {
        SERVER_DATA.hidden = true;
    } else {
        SERVER_DATA_TITLE.innerText = `Information for ${selected_server}`;
        SERVER_DATA_LOG.innerText = server_data.running_data.log;
        SERVER_DATA.hidden = false;
    }
}

function get_running_server(server_name) {
    for (const server of running_servers) {
        if (server.name === server_name) {
            return server;
        }
    }
    return null;
}

function is_server_running(server_name) {
    return get_running_server(server_name) !== null;
}

function init() {
    if (is_logged_in()) {
        fetch_servers();
        setInterval(fetch_servers, 4000);
    }
}


window.onload = () => init();