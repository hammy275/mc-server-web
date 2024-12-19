import {Button, Col, Container, Navbar, Row} from "react-bootstrap";
import {login, logout, post} from "./util.ts";
import {useState} from "react";

type HeaderProps = {
    name : string | null;
    is_admin : boolean;
}

async function signInOutClick(signed_in: boolean) {
    if (signed_in) {
        await logout();
    } else {
        login();
    }
}

const Header = (props : HeaderProps)=> {
    const right_text = props.name !== null ? "Hello " + props.name + "!" : "";
    const sign_text = props.name !== null ? "Sign Out" : "Sign In";
    const html = document.getElementById("html");
    const theme = html?.getAttribute("data-bs-theme");
    const [isDark, setDark] = useState(localStorage.getItem("dark") !== "false"); // null is also dark, since that's the default
    const refreshServers = props.is_admin ?
        <Col xs="auto">
            <Button variant="warning" onClick={() => post("/api/refresh_servers")}>
                Refresh Available Servers
            </Button>
        </Col>
        : <></>;
    return (
        <Navbar expand="lg" className="bg-body-tertiary">
            <Container>
                <Navbar.Brand>MC Server Web</Navbar.Brand>
                <Navbar.Toggle></Navbar.Toggle>
                <Navbar.Collapse className="justify-content-end">
                    <Navbar.Text>{right_text}</Navbar.Text>
                    <Row>
                        <Col xs="auto">
                            <br/>
                        </Col>
                        <Col xs="auto">
                            <Button variant={isDark ? "light" : "dark"} onClick={() => {
                                html?.setAttribute("data-bs-theme", isDark ? "light" : "dark");
                                localStorage.setItem("dark", (!isDark).toString());
                                setDark(!isDark);
                            }}>Switch Theme</Button>
                        </Col>
                        {refreshServers}
                        <Col xs="auto">
                            <Button variant="secondary" onClick={() => {
                                localStorage.removeItem("useNewSite");
                                window.location.href = "/index.html";
                            }}>Use Old Site</Button>
                        </Col>
                        <Col xs="auto">
                            <Button onClick={() => signInOutClick(props.name !== null)} type="submit">{sign_text}</Button>
                        </Col>
                    </Row>
                </Navbar.Collapse>
            </Container>
        </Navbar>
    );
}

export default Header;