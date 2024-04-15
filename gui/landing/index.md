---
layout: base
permalink: /
type: network
title: GURU Network
description: "At DexGuru, we're not just building a platform; we're shaping the future of blockchain technology. From our origins as a pioneering Dex Aggregator to our evolution into a comprehensive AI-enhanced blockchain ecosystem, DexGuru stands at the forefront of innovation, ready to unlock the full potential of decentralized applications for developers, AI enthusiasts, and blockchain believers alike."
# --------------------------
# start: Banner config
banner:
  type: network
  title: GURU Network
  subtitle: Orchestrating Multi-Step <b>Ai Processors</b> and <br /><b>RAG</b>(Retrieval-Augmented Generation) Applications OnChain

  actions:
    - {
        title: Book a Demo,
        url: https://webforms.pipedrive.com/f/c6vRxuvEjYqAxWSu1hN3xF2Cm5KyUtB66yKiko2wxKvPIs2J5R6mPJUV3oMdjnoHpF,
        type: book,
      }
    - { title: Participate in LBP, url: https://dex.guru, type: book }

  text: "The GURU Network provides a transformative platform for startup innovators and dApp builders, integrating AI and blockchain technologies to simplify the development process and operations of startup as a business."

partners:
  subtitle: We secured a total of $6 million through two successful venture capital rounds to develop a sophisticated trading terminal and deliver dependable market data.
---

<!-- REVOLUTION SECTION -->

{% capture content %}

For Application developers it’s became expected that they embed GPT mechanics, and market is growing as well as workforce is forced to use AI Processors more in more in daily routines, points:

- People became used to GPT flow mechanics.
- If you’re building in 2024 you expected to have GPT/AI Mechanics implemented in your application.
- Retrieval-Augmented Generation(RAG) applications enhancing GPT output by integrating external information retrieval widely appearing as portion of help/service desk business processes.
- Multi-step AI Processors are used by professional GPT users in their daily activities and work life.
- We believe projects driving GTP Revolution towards utilization of financial tooling of Web3 World would prevail in this cycle.

{% endcapture %}

{% include section.html pretitle="GPT Revolution" title="Happened Now What?" text=content  img="/assets/img/content/revolution.svg" align="left" bg="light" animate=true %}

<!-- / REVOLUTION SECTION -->

{% include section.html pretitle="GURU Platform and Network" title="Scaling dApps Ecosystem" img="/assets/img/content/scaling.svg" %}

{% include vision.html %}

{% include howworks.html %}

<!-- ORCHESTRATOR SECTION -->

{% capture content %}

Orchestrator is in a core of GURU Platform Ecosystem powering up all connection and financial means of GURU Network:

- Provides single execution context for variety of environments (on-chain/off-chain/user/AI interactions)
- Seamlessly orchestrate multi-steps LLM/AI models using orchestration snippets catalog
- Reuse Published BPA Definitions
- Distribute Execution when working in pair with GURU Wallet, which allows remote execution from FlowOrchestration on particular actions.
- EventBus exposed on GURU Network as an Oracle

{% endcapture %}

{% include section.html pretitle="Flow Orchestrator" title="Processes as a service" text=content  img="/assets/img/content/revolution.svg" align="left" bg="dark" %}

<!-- / ORCHESTRATOR SECTION -->

<!-- SDK SECTION -->

{% capture content %}

GURU Wallet and Wallet SDK serves as a window into GURU Network participation, as a builder, user or compute node runner. Wallet SDK is the main interface to communicate with Network and control all the processes/projects attached to the account. Same time it serves as a view into GURU Network Ecosystem, like and Ecosystem App Store if you want.

- GURU Wallet SDK: Acts as an Eternal Worker for process orchestration within the GURU Network. Allowing users to orchestrate non-custodial trading mechanics.
- Orchestrated Process Execution: Seamlessly trigger actions and manage smart contracts through FlowOrchestrator integration.
- Personalized AI Processors: Deploy and control BPAs from applications catalog, as Personal Assistants for enhanced productivity across the ecosystem.
- Earn When Idle: Users contribute computational power to run AI models, selected based on device performance to fulfill SLA. Devices answer GPT Model questions during idle times, like overnight charging, earning rewards for users.
- GURU Ecosystem role: Cornerstone component in realizing Guru Labs' vision for a decentralized, efficient, and user-centric digital world.

{% endcapture %}

{% include section.html pretitle="GURU Wallet SDK" title="Gateway To Participate" text=content img="/assets/img/content/sdk.svg" align="right"  %}

<!-- / SDK SECTION -->

{% include network.html  %}

{% include section.html pretitle="GURU Network" title="Tokenomics" img="/assets/img/content/tokenomics.svg" bg="dark" %}

{% include distribution.html  %}

{% include section.html title="Roadmap" img="/assets/img/content/roadmap.svg" bg="light"   %}

{% include section.html pretitle="GURU Network" title="Ecosystem Markets" img="/assets/img/content/market.svg" bg="dark" %}

{% include adopters.html %}

{% include section.html title="Go to Market Strategy" img="/assets/img/content/strategy.svg" bg="light" %}
