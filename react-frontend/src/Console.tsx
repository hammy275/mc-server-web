type ConsoleProps = {
    log : string;
}

const Console = (props : ConsoleProps) => {
    return (
        <>
            <span style={{"whiteSpace": "pre-line"}}>{props.log}</span>
        </>
    )
}

export default Console;