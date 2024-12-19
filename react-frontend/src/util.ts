export async function post(url : string, data : object | null = null, show_alert : boolean = true) : Promise<Array<any>> {
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
        alert(resp_data.message);
    }
    return [resp_data, resp.status];
}

export function login() {
    window.location.href = "/auth/authorize";
}

export async function logout() {
    await post("/auth/logout", null, false);
    location.reload();
}