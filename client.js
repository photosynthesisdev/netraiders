// Adds an entry to the event log on the page, optionally applying a specified
// CSS class.

let currentTransport, streamNumber, currentTransportDatagramWriter;
let currentWebsocket;

// "Connect" button handler.
async function connect() {
  const url = "https://dilate.ai:4433/counter";
  try {
    var transport = new WebTransport(url);
    addToEventLog('Initiating connection...');
  } catch (e) {
    addToEventLog('Failed to create connection object. ' + e, 'error');
    return;
  }

  try {
    await transport.ready;
    addToEventLog('Connection ready.');
  } catch (e) {
    addToEventLog('Connection failed. ' + e, 'error');
    return;
  }

  transport.closed
      .then(() => {
        addToEventLog('Connection closed normally.');
      })
      .catch(() => {
        addToEventLog('Connection closed abruptly.', 'error');
      });

  currentTransport = transport;
  streamNumber = 1;
  try {
    currentTransportDatagramWriter = transport.datagrams.writable.getWriter();
    addToEventLog('Datagram writer ready.');
  } catch (e) {
    addToEventLog('Sending datagrams not supported: ' + e, 'error');
    return;
  }
  readDatagrams(transport);
  document.forms.sending.elements.send.disabled = false;
  document.getElementById('connect').disabled = true;
}

// "Connect" button handler for WebSocket.
function connectWS() {
  const url = "wss://dev.supertrip.land/api/wsTest";
  try {
    var ws = new WebSocket(url);
    addToEventLog('Initiating WS connection...');
    
    ws.onopen = function() {
      addToEventLog('WS connection established.');
      currentWebsocket = ws;
      // Enable UI elements related to WebSocket communication here, if any.
      document.getElementById('connectWS').disabled = true; // Assuming 'connectWS' is your button ID for WebSocket connection.
      document.forms.sendWebsocket.elements.sendWebsocket.disabled = false;
    };
    
    ws.onerror = function(error) {
      addToEventLog('WebSocket error: ' + error.message, 'error');
    };
    
    ws.onclose = function(event) {
      addToEventLog('WebSocket connection closed.' + event.code + event.reason);
      // Disable or reset UI elements related to WebSocket communication here, if needed.
    };

    ws.addEventListener("message", (event)=>{
      console.log("Message from server ", event.data);
      addToEventLog('Received message: ' + event.data);
    });
    
    // Example of handling incoming WebSocket messages.
    //ws.onmessage = function(event) {
    //  console.log(event.data);
      // Handle incoming message contained in event.data
    //  addToEventLog('Received message: ' + event.data);
    //};

  } catch (e) {
    addToEventLog('Failed to create WS connection object. ' + e, 'error');
    return;
  }
}

async function runPerformanceTests() {
  const encoder = new TextEncoder('utf-8');
  const sampleJson = JSON.stringify({
    exampleData: 'This is an example JSON payload for the performance test over a minute.'
  });
  const data = encoder.encode(sampleJson);

  let sentPackets = 0;
  let acknowledgedPackets = 0;
  const startTime = Date.now();
  const duration = 60000; // 60 seconds in milliseconds
  const packetsPerSecond = new Array(60).fill(0); // Track packets sent per second

  // Assuming an asynchronous function to simulate packet acknowledgment
  async function receiveAcknowledgment() {
    // Simulate variable network delay
    await new Promise(resolve => setTimeout(resolve, Math.random() * 100));
    acknowledgedPackets++;
  }

  try {
    while (Date.now() - startTime < duration) {
      // Send a packet
      currentTransportDatagramWriter.write(data).then(() => {
        sentPackets++;
        const secondIndex = Math.floor((Date.now() - startTime) / 1000);
        packetsPerSecond[secondIndex] = (packetsPerSecond[secondIndex] || 0) + 1;
        receiveAcknowledgment(); // Simulate receiving an acknowledgment
      }).catch(e => {
        addToEventLog('Error while sending data: ' + e, 'error');
      });

      // Introduce a small delay to regulate sending rate
      await new Promise(resolve => setTimeout(resolve, 10));
    }

    // Allow some time for the last acknowledgments to arrive
    await new Promise(resolve => setTimeout(resolve, 1000));

    addToEventLog(`Test completed: Sent ${sentPackets} packets, Acknowledged ${acknowledgedPackets} packets.`);
    addToEventLog(`Packet Loss: ${(1 - acknowledgedPackets / sentPackets) * 100}%`);
    packetsPerSecond.forEach((pps, second) => {
      addToEventLog(`Second ${second + 1}: ${pps} packets`);
    });

    // Calculate average packets per second
    const avgPacketsPerSecond = sentPackets / 60;
    addToEventLog(`Average packets per second: ${avgPacketsPerSecond}`);
  } catch (e) {
    addToEventLog('Error while running performance tests: ' + e, 'error');
  }
}

function runPerformanceTestWebsocket() {
  if (!currentWebsocket || currentWebsocket.readyState !== WebSocket.OPEN) {
    addToEventLog('WebSocket is not connected.', 'error');
    return;
  }

  const sampleJson = JSON.stringify({
    exampleData: 'This is an example JSON payload for the WebSocket performance test.'
  });

  let sentPackets = 0;
  let acknowledgedPackets = 0;
  let startTime = Date.now();
  const duration = 60000; // 60 seconds in milliseconds
  const packetsPerSecond = new Array(60).fill(0); // Track packets sent per second

  const intervalId = setInterval(() => {
    if (Date.now() - startTime >= duration) {
      clearInterval(intervalId);
      // Optionally close the WebSocket after the test or leave it open for other uses
      // currentWebsocket.close();
      return;
    }

    currentWebsocket.send(sampleJson);
    sentPackets++;
    const secondIndex = Math.floor((Date.now() - startTime) / 1000);
    packetsPerSecond[secondIndex] = (packetsPerSecond[secondIndex] || 0) + 1;
  }, 10);

  // Adjust onmessage handler to count acknowledgments
  currentWebsocket.onmessage = (event) => {
    // Assuming the server sends back a simple acknowledgment for each message
    acknowledgedPackets++;
  };

  // Optional: Adjust onclose handler for the test context
  currentWebsocket.onclose = () => {
    clearInterval(intervalId); // Stop sending data if the WebSocket is closed prematurely
    addToEventLog(`WebSocket connection closed during the test.`);
  };

  // Optional: Adjust onerror handler for the test context
  currentWebsocket.onerror = (error) => {
    addToEventLog(`WebSocket error during the test: ${error}`, 'error');
  };

  // Optionally add a completion handler or other logic after the test duration
  setTimeout(() => {
    addToEventLog(`Test completed: Sent ${sentPackets} packets, Acknowledged ${acknowledgedPackets} packets.`);
    addToEventLog(`Packet Loss: ${(1 - acknowledgedPackets / sentPackets) * 100}%`);
    packetsPerSecond.forEach((pps, second) => {
      addToEventLog(`Second ${second + 1}: ${pps} packets`);
    });

    // Calculate and log average packets per second
    const avgPacketsPerSecond = sentPackets / 60;
    addToEventLog(`Average packets per second: ${avgPacketsPerSecond}`);
  }, duration);
}



// Reads datagrams from |transport| into the event log until EOF is reached.
async function readDatagrams(transport) {
  try {
    var reader = transport.datagrams.readable.getReader();
    addToEventLog('Datagram reader ready.');
  } catch (e) {
    addToEventLog('Receiving datagrams not supported: ' + e, 'error');
    return;
  }
  let decoder = new TextDecoder('utf-8');
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) {
        addToEventLog('Done reading datagrams!');
        return;
      }
      let data = decoder.decode(value);
      addToEventLog('Datagram received: ' + data);
    }
  } catch (e) {
    addToEventLog('Error while reading datagrams: ' + e, 'error');
  }
}


function addToEventLog(text, severity = 'info') {
  let log = document.getElementById('event-log');
  let mostRecentEntry = log.lastElementChild;
  let entry = document.createElement('li');
  entry.innerText = text;
  entry.className = 'log-' + severity;
  log.appendChild(entry);

  // If the most recent entry in the log was visible, scroll the log to the
  // newly added element.
  if (mostRecentEntry != null &&
      mostRecentEntry.getBoundingClientRect().top <
          log.getBoundingClientRect().bottom) {
    entry.scrollIntoView();
  }
}
