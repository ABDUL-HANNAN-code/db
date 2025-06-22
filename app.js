
// Example: Test backend connectivity
async function testBackendConnection() {
    try {
        const response = await fetch("http://localhost:8000/api/health", {
            method: "GET",
        });
        const data = await response.json();
        document.getElementById("api-result").innerText = JSON.stringify(data);
    } catch (error) {
        document.getElementById("api-result").innerText = "Failed to connect: " + error;
    }
}

window.onload = testBackendConnection;
