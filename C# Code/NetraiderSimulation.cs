using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace NetRaiders {
    public class NetraiderSimulation
    {

        /// What is most recent authoritative player state from the server.
        public NetraiderPlayer local_player;

        /// How many ticks per second is simulation running at? This is told to us by the server.
        public int TickRate => local_player.tick_rate;

        /// How many seconds is a tick?
        public float TickInSeconds => 1.0f / TickRate;

        /// When was the most recent authoritative tick?
        public int AuthoritativeTick => local_player.tick;

        public int LocalTick { get; private set; }

        /// What is the our RTT, in terms of ticks?
        public int TickRTT => local_player.tick;

        /// Authoritative Position of the player.
        public Vector3 AuthoritativePosition { get; private set; }

        // declaring some basic things.
        private double last_unix_update_received;
        private NetraiderWebsocket netraiderWebsocket;
        private static DateTime epoch_start = new DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc);

        public NetraiderSimulation(NetraiderPlayer inital_simulation_state, NetraiderWebsocket netraiderWebsocket) {
            // Simulation can only start once we receive our inital state.
            this.netraiderWebsocket = netraiderWebsocket;
            ReceiveSimulationUpdate(inital_simulation_state);
        }

        internal double GetUnixTime()
        {
            double unix_time = (DateTime.UtcNow - epoch_start).TotalSeconds;
            return unix_time;
        }

        /// <summary>
        /// Called by Websocket when we receive the most recent up to date state of our player from the server.
        /// </summary>
        /// <param name="local_player"></param>
        public void ReceiveSimulationUpdate(NetraiderPlayer local_player)
        {
            Debug.Log("Receiving Simulation Updates");
            this.local_player = local_player;
            this.LocalTick = local_player.tick; // set local tick to authoritative state.
            this.AuthoritativePosition = new Vector3(local_player.x, local_player.y, local_player.z);
            this.last_unix_update_received = GetUnixTime();
        }

        public void UpdateClientSimulation()
        {
            this.LocalTick += 1; 
        }


        /// <summary>
        /// Called by NetraiderConnect coroutine when we are ready to send inputs.
        /// </summary>
        /// <param name="netraiderInput"></param>
        public void SendInputsToServer(NetraiderInput netraiderInput) {
            // We can safely assume that the server is currently on TickRTT / 2, so mark our netraider input with that frame.
            UpdateClientSimulation();
            float half_rtt = (TickRTT / 2);
            netraiderInput.expected_tick = LocalTick + half_rtt;
            // Send inputs to the server;
            this.netraiderWebsocket.SendInputs(netraiderInput);
        }
    }
}

