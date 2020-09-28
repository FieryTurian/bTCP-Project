# bTCP-Project

Group:
- Onno de Gouw
- Stefan Popa

---------------------------------------------------------------------

In this project, we have implemented the sending and receiving transport-level code for a reliable data transfer protocol that we call bTCP, short for basic Transmission Control Protocol, which borrows a number of features from TCP. It guarantees reliable delivery of application layer data to the destination host, it provides flow control and it is connection oriented. Connections are established through a three-way handshake and tore down through a different kind of handshake.

The testing framework includes the following tests:
1. ideal network (no packet loss, bit flips, etc);
2. network with spurious bit flips;
3. network with duplicate packets;
4. network with packet loss;
5. network with delays (sometimes exceeding the timeout value);
6. network with reordered packets;
7. network with all of the above problems;

The project was made for the course Networks and Distributed Systems at Radboud University, cohort 2018.

Note: lossy_layer.py and testframework.py were mostly implemented by the professors of the course.
