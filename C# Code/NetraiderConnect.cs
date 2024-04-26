using System;
using System.Collections;
using System.Collections.Generic;
using NativeWebSocket;
using UnityEngine;

namespace NetRaiders
{
    public struct NetraiderInput
    {
        public float expected_tick;
        public bool up;
        public bool down;
        public bool left;
        public bool right;
    }
    public class NetraiderPlayer
    {
        public short user_id;
        public string username;
        public int tick;
        public int tick_rtt;
        public int tick_rate;
        public float speed;
        public float x;
        public float y;
        public float z;
    }

    public class NetraiderConnect : MonoBehaviour
    {

        public static NetraiderConnect Instance;
        public NetraiderPlayer LocalNetRaider;
        public NetraiderSimulation Simulation => netraiderWebsocket.netraiderSimulation;

        private NetraiderInput netRaiderInput;
        private NetraiderWebsocket netraiderWebsocket;

        private void Awake() {
            if (Instance) {
                Destroy(gameObject);
                return;
            }
            Instance = this;
        }

        private void Start() {
            ConnectToSocket();
            StartCoroutine(TickTimer());
        }

        IEnumerator TickTimer() {
            while (netraiderWebsocket.netraiderSimulation == null) {
                yield return null; // Wait for the simulation to begin.. (to here from server start signal)
            }
            while (true) {
                /// Send inputs every tick.
                Debug.Log($"sending inputs: {netraiderWebsocket.netraiderSimulation.TickInSeconds}");
                netraiderWebsocket.netraiderSimulation.SendInputsToServer(ConsumeInput());
                /// Wait one the time of one tick
                yield return new WaitForSeconds(netraiderWebsocket.netraiderSimulation.TickInSeconds);
            }
        }

        private void ConnectToSocket() {
            netraiderWebsocket = new();
            netraiderWebsocket.Connect("ws://spock.cs.colgate.edu/api/netraiderConnect");
        }

        private void Update() {
#if !UNITY_WEBGL || UNITY_EDITOR
            if(netraiderWebsocket != null && netraiderWebsocket.webSocket != null && netraiderWebsocket.webSocket.State != WebSocketState.Closed && netraiderWebsocket.webSocket.State != WebSocketState.Closing)
            {
                netraiderWebsocket.webSocket.DispatchMessageQueue();
            }
#endif
            if (netraiderWebsocket.webSocket.State == WebSocketState.Closed)
            {
              //  ConnectToSocket();
            }
        }
        /// Netraider connect serves to collect inputs.
        
        public void PressUp() => netRaiderInput.up = true;
        public void PressDown() => netRaiderInput.down = true;
        public void PressLeft() => netRaiderInput.left = true;
        public void PressRight() => netRaiderInput.right = true;

        public NetraiderInput ConsumeInput() {
            NetraiderInput inputs = netRaiderInput;
            netRaiderInput = new(); //Resets input
            return inputs;
        }
    }
}
