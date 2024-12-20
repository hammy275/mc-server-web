import { Form } from "react-bootstrap";
import {useState} from "react";
import {post} from "./util.ts";

type ConsoleProps = {
    log : string;
    admin : boolean;
    server : string;
}

const Console = (props : ConsoleProps) => {
    const [command, setCommand] = useState("");
    async function onKeyDown(event: any) {
        if (event.key === "Enter") {
            if (command !== "") {
                await post("/api/run_command", {"name": props.server, "command": command}, false);
                setCommand("");
            }
        }
    }
    const input = props.admin ?
        <Form.Control placeholder="Enter Command..." value={command} onChange={(event) => setCommand(event.target.value)} onKeyDown={onKeyDown} id="commandInput"></Form.Control>
        : <></>;
    return (
        <>
            <span style={{"whiteSpace": "pre-line"}}>{props.log}</span>
            {input}
        </>
    )
}

export default Console;