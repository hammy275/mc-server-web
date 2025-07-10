import {Button, Col, FloatingLabel, Form, ListGroup, Row} from "react-bootstrap";
import {post} from "./util.ts";

type ServerSelectionProps = {
    server : string;
    servers : Array<any>;
    setServer : (server : string) => void;
    onServerStartStop : () => void;
}

const ServerSelection = (props : ServerSelectionProps) => {

    async function startStopServer() {
        const action = serverStarted(props.server) ? "stop" : "start";
        await post("/api/manage", {"name": props.server, "action": action});
        props.onServerStartStop();
    }

    function serverStarted(server: string) {
        for (const s of props.servers) {
            if (s.name === server) {
                return s.running;
            }
        }
        return false;
    }

    function serverHasModpack(server: string) {
        for (const s of props.servers) {
            if (s.name === server) {
                return s.has_modpack;
            }
        }
        return false;
    }

    function downloadModpack(server: string) {
        console.log(server);
    }

    const serverOpen = serverStarted(props.server);
    const button = <Button onClick={startStopServer}
                           variant={serverOpen ? "danger" : "success"}>{serverOpen ? "Stop Server" : "Start Server"}</Button>
    const runningServers = props.servers.filter(server => server.running);
    const runningServersHeader = runningServers.length === 0 ? <></> : <h2>Running Servers:</h2>;
    return (
        <>
            <Col>
                <Row className="align-items-center">
                    <Col>
                        <FloatingLabel controlId="floatingSelect" label="Select a Server">
                            <Form.Select onChange={(e) => props.setServer(e.target.value)} value={props.server}
                                         aria-label="Select a Server" id="server_select">
                                {props.servers.map((server) => (
                                    <option value={server.name}>{server.name}</option>
                                ))}
                            </Form.Select>
                        </FloatingLabel>
                    </Col>
                    <Col xs={2}>
                        {button}
                    </Col>
                    <Col>
                        <Button disabled={!serverHasModpack(props.server)} variant="primary"
                                href={`/api/download_modpack?name=${props.server}`}>Download Modpack</Button>
                    </Col>
                </Row>
            </Col>
            <br/>
            <Col>
                {runningServersHeader}
                <ListGroup>
                    {runningServers.map((server) => (
                        <ListGroup.Item action
                                        onClick={() => props.setServer(server.name)}>{server.name}</ListGroup.Item>
                    ))}
                </ListGroup>
            </Col>
        </>
    );
}

export default ServerSelection;