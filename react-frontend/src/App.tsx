import Header from "./Header.tsx";
import {useEffect, useState} from "react";
import ServerSelection from "./ServerSelection.tsx";
import {Button, Col, Container, Modal, Row} from "react-bootstrap";
import Console from "./Console.tsx";
import {post} from "./util.ts";

function App() {
    const [name, setName] = useState<string | null>(null);
    const [isAdmin, setIsAdmin] = useState(false);
    const [server, setServer] = useState<string>("");
    const [servers, setServers] = useState<Array<any>>([]);
    const [log, setLog] = useState<string>("");
    const [didInit, setDidInit] = useState(false);
    const [alert, setAlert] = useState("");
    if (!localStorage.getItem("useNewSite")) {
        window.location.href = "/index.html";
    }
    async function init() {
        const html = document.getElementById("html");
        const darkFromStorage = localStorage.getItem("dark");
        if (html !== null && darkFromStorage !== null) {
            html.setAttribute("data-bs-theme", darkFromStorage === "true" ? "dark" : "light")
        } else if (html !== null) {
            localStorage.setItem("dark", "true");
        }
        const data = await (await fetch("/auth/info")).json();
        setDidInit(true);
        setName(data.name);
        setIsAdmin(data.admin);
        await updateServersAndLog();
    }
    async function updateServersAndLog() {
        const [data, status] = await post("/api/list", null, false);
        if (status === 200) {
            setServers(data.data);
            // Ensures dropdown state is matched to what's shown on first page load
            if (server === "") {
                setServer(data.data[0].name);
            }
        } else {
            setServers([]);
        }
    }
    async function onSetServer(server : string) {
        setServer(server);
        await updateServersAndLog();
    }
    useEffect(() => {
        if (!didInit) {
            init();
        }
        let newLog = "";
            for (const s of servers) {
                if (s.name === server) {
                    if (s.running) {
                        newLog = s.log === null ? "" : s.log;
                        break;
                    }
                }
            }
            setLog(newLog);
        const interval = setInterval(updateServersAndLog, 3000);
        return () => clearInterval(interval);
    });
    const loggedInPage = name !== null ? (
        <Container fluid>
            <br/>
            <Row>
                <Col xs={1}></Col>
                <Col>
                    <ServerSelection onServerStartStop={updateServersAndLog} servers={servers} setServer={onSetServer} server={server}/>
                </Col>
                <Col>
                    <Console log={log}/>
                </Col>
                <Col xs={1}></Col>
            </Row>
        </Container>
    ) : <></>
    window.alert = setAlert; // Dirty hack to let us use window.alert for modals
    return (
    <>
        <Header is_admin={isAdmin} name={name}/>
        {loggedInPage}
        <Modal show={alert !== ""} onHide={() => setAlert("")}>
            <Modal.Header closeButton>
                <Modal.Title>{alert}</Modal.Title>
            </Modal.Header>
            <Modal.Footer>
                <Button variant="primary" onClick={() => setAlert("")}>
                    Ok
                </Button>
            </Modal.Footer>
        </Modal>
    </>
    )
}

export default App
