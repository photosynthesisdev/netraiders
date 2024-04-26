using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace NetRaiders
{
    public class Character : MonoBehaviour
    {
        public static Character Instance;

        private void Awake()
        {
            Instance = this;
        }

        // Gathers input.
        private void Update()
        {
            if (NetraiderConnect.Instance == null || NetraiderConnect.Instance.Simulation == null) {
                return;
            }
            if (Input.GetKey(KeyCode.W))
            {
                NetraiderConnect.Instance.PressUp();
            }
            if (Input.GetKey(KeyCode.A))
            {
                NetraiderConnect.Instance.PressLeft();
            }
            if (Input.GetKey(KeyCode.S))
            {
                NetraiderConnect.Instance.PressDown();
            }
            if (Input.GetKey(KeyCode.D))
            {
                NetraiderConnect.Instance.PressRight();
            }
            transform.localPosition = NetraiderConnect.Instance.Simulation.AuthoritativePosition;
        }
    }
}
