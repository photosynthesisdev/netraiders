using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using NativeWebSocket;

namespace NetRaiders
{
    public class NetraiderWebsocket
    {
        public NetraiderSimulation netraiderSimulation;
        public WebSocket webSocket;
        public bool socketAccepted;
        public WebSocketCloseCode WebSocketCloseCode;

        public async void Connect(string url)
        {
            if (webSocket != null && webSocket.State != WebSocketState.Closed)
            {
                return;
            }
            webSocket = new WebSocket(url);
            webSocket.OnOpen += () =>
            {
                Debug.Log("Socket Connected");
            };
            webSocket.OnMessage += async (bytes) =>
            {
                string data = System.Text.Encoding.UTF8.GetString(bytes);
                if (data == "ping") {
                    await webSocket.SendText("pong");
                    return;
                }
                NetraiderPlayer responsePlayer = JsonUtility.FromJson<NetraiderPlayer>(data);
                if (netraiderSimulation == null) {
                    netraiderSimulation = new NetraiderSimulation(responsePlayer, this);
                    return;
                }
                netraiderSimulation.ReceiveSimulationUpdate(responsePlayer);
            };
            // Handle Errors
            webSocket.OnError += (e) => Debug.LogError($"STAGE Txn WebSocket Error: {e}");
            // Close socket when ready to close.
            webSocket.OnClose += (e) => {
                Debug.Log(e);
                WebSocketCloseCode = e;
                socketAccepted = false;
            };
            await webSocket.Connect();
        }

        public async void Disconnect()
        {
            if (webSocket != null && webSocket.State != WebSocketState.Closed)
            {
                await webSocket.Close();
            }
        }

        // THIS GETS CALLED EVERY TICK.
        public async void SendInputs(NetraiderInput consumeInput)
        {
            await webSocket.SendText(JsonUtility.ToJson(consumeInput));
        }

    }
}
