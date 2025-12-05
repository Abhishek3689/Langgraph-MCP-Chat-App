from fastmcp import FastMCP

mcp=FastMCP(name="calculator server")

@mcp.tool
def arithmatic_calci(a, b, operation):
    """
    Perform arithmetic operation. Accepts +,-,*,/, multiply, add, subtract, divide.
    Always returns JSON object.
    """
    try:
        if operation == '+' or operation=='add':
            return {"result": a + b}

        elif operation == '-' or operation=='subtract':
            return {"result": a - b}

        elif operation == '*' or operation=='multiply' or operation=='product':
            return {"result": a * b}

        elif operation == '/' or operation=='divide':
            if b == 0:
                return {"error": "Division by zero"}
            return {"result": a / b}

        else:
            return {"error": "Unsupported operation"}

    except Exception as e:
        return {"error": str(e)}


if __name__=='__main__':
    mcp.run()