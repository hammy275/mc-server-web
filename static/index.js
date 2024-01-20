const SERVER_LIST = document.getElementById("server_list")

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

async function start_server() {
    const name = SERVER_LIST.value;
    const resp = await post("/api/run", {"name": name});
}

function login() {
    window.location.href = "/auth/authorize"
}

async function logout() {
    await post("/auth/logout");
    location.reload();
}

async function init() {
    const resp = await post("/api/list");
    if (resp[1] === 200) {
        const server_list = resp[0].data;
        for (const server of server_list) {
            const opt = document.createElement("option");
            opt.text = server;
            SERVER_LIST.add(opt);
        }
        SERVER_LIST.remove(0);
    } else {
        const opt = document.createElement("option");
        opt.text = "Not Logged In!";
        SERVER_LIST.add(opt);
        SERVER_LIST.remove(0);
    }
}


window.onload = () => init();