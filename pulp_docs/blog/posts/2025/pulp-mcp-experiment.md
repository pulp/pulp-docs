---
date: 2025-06-23T09:00:00+03:00
title: "Bridging Worlds: Interacting with LLMs in an MCP Server for Pulp (and the Realities of Local Hardware)"
authors:
  - decko
tags:
  - ai
  - mcp
  - llama
  - llm
---

Alright team, and everyone in our awesome Pulp community!

Gather 'round, because I've got a cool project to tell you about – something I've been tinkering with that brings our beloved **Pulp API** into the wild west of LLMs. Imagine being able to chat with an AI, asking it to list your repos, upload content, or maybe even publish a new version, all by just typing out what you want. That's been the dream I've been chasing!

I've been building a **Model Context Protocol (MCP) server** that lets a user interact with an LLM (Large Language Model) directly, and here's the kicker: this MCP server was specifically designed to **talk to the Pulp API!** How cool is that?

<!-- more -->

Let's break down the ingredients of this digital stew:

### The Secret Sauce: What Made This Possible

First, a quick intro to the tech I wrangled:

* **Model Context Protocol (MCP):** So, imagine LLMs are super smart but need a manual to interact with the world outside their brain. **MCP is that manual**. It's a fancy way to let LLMs know about "resources" (like, "hey, here's what a repository looks like in Pulp") and "tools" (like, "you can use this 'create_repo' tool to make a new one!"). This structured chat helps the AI actually *do* things, not just talk about them.

* **[FastMCP](https://github.com/jlowin/fastmcp):** Building an MCP server from scratch is like trying to build a spaceship with a screwdriver. **FastMCP is the easy button for Python**. It handles all the nitty-gritty details of the MCP spec, so I could focus on telling the LLM what Pulp can do. It's like having a LEGO set specifically for MCP servers – way easier than carving your own bricks!

* **[Ollama](https://ollama.com/):** Ever wanted to run a super-smart AI on your own machine without sending all your data to the cloud? That's **Ollama**! It makes downloading and running LLMs locally a breeze. Privacy, speed, and no surprise bills – what's not to love? This was crucial for keeping everything in-house.

* **[Llama Stack](https://www.llama.com/products/llama-stack/):** Think of **Llama Stack** as the ultimate connector kit for AI. It's not just one thing; it's a whole ecosystem of tools that helps you build, scale, and deploy generative AI apps. In my setup, Llama Stack was the bridge, making sure my FastMCP server could seamlessly chat with the Ollama-powered LLM. It's like the perfect multi-tool for the Llamaverse.

---

### My Grand Experiment: Pulp, Meet LLM!

The big idea was simple: create an MCP server where you could type into a chat, and an LLM would understand your Pulp-related requests and respond accordingly. The goal wasn't just chit-chat, but actually performing actions via the Pulp API!

Here's the simplified flow:

You type a message (e.g., "list all my repositories") -> **Llama Stack** (sends your request to Ollama) -> **Ollama** (our LLM brain processes your request and figures out the Pulp API call) -> **Llama Stack** (sends the Pulp API call back) -> **FastMCP Server** (makes the *actual* Pulp API call!) -> Pulp responds -> FastMCP Server gets the result.

```
 '====================================================================================================\n'
 'Processing user query: Can you list all domains again?\n'
 '====================================================================================================')
INFO:httpx:HTTP Request: POST http://localhost:8321/v1/agents/f83b1eb7-13df-47a9-89ed-f5e271b02c93/session/f64f5501-ea81-408b-a299-2cd0c5b0bd58/turn "HTTP/1.1 200 OK"
inference> [get_pulp_domains(session_id="")]
tool_execution> Tool:get_pulp_domains Args:{'session_id': ''}
tool_execution> Tool:get_pulp_domains Response:[TextContentItem(text='{\n  "success": true,\n  "result": {\n    "count": 2,\n    "next": null,\n    "previous": null,\n    "results": [\n      {\n        "pulp_href": "/pulp/default/api/v3/domains/019794aa-fc21-7e6b-a325-f4d535e4fafd/",\n        "prn": "prn:core.domain:019794aa-fc21-7e6b-a325-f4d535e4fafd",\n        "pulp_created": "2025-06-21T22:45:23.105767Z",\n        "pulp_last_updated": "2025-06-21T22:45:23.105775Z",\n        "name": "pulp-mcp-test",\n        "description": null,\n        "pulp_labels": {},\n        "storage_class": "pulpcore.app.models.storage.FileSystem",\n        "storage_settings": {\n          "hidden_fields": [],\n          "location": "/var/lib/pulp/media/",\n          "base_url": "",\n          "file_permissions_mode": 420,\n          "directory_permissions_mode": null\n        },\n        "redirect_to_object_storage": true,\n        "hide_guarded_distributions": false\n      },\n      {\n        "pulp_href": "/pulp/default/api/v3/domains/a1d64603-a91f-40f1-b3b2-9f2fb3bbb835/",\n        "prn": "prn:core.domain:a1d64603-a91f-40f1-b3b2-9f2fb3bbb835",\n        "pulp_created": "2025-06-20T14:17:27.991915Z",\n        "pulp_last_updated": "2025-06-20T14:17:27.991922Z",\n        "name": "default",\n        "description": null,\n        "pulp_labels": {},\n        "storage_class": "pulpcore.app.models.storage.FileSystem",\n        "storage_settings": {\n          "hidden_fields": [],\n          "location": "/var/lib/pulp/media",\n          "base_url": "/",\n          "file_permissions_mode": 420,\n          "directory_permissions_mode": null\n        },\n        "redirect_to_object_storage": true,\n        "hide_guarded_distributions": false\n      }\n    ]\n  }\n}', type='text')]

inference> There are two domains in Pulp. The first domain is named 'pulp-mcp-test' and the second one is named 'default'.

```
or

```
 '====================================================================================================\n'
 'Processing user query: Can you create a new rpm repository named '
 "'pulp-mcp-test-rpm-repo' for the domain we just created?\n"
 '====================================================================================================')
INFO:httpx:HTTP Request: POST http://localhost:8321/v1/agents/f83b1eb7-13df-47a9-89ed-f5e271b02c93/session/f64f5501-ea81-408b-a299-2cd0c5b0bd58/turn "HTTP/1.1 200 OK"
inference> [create_rpm_repository(domain="pulp-mcp-test", name="pulp-mcp-test-rpm-repo", remote="", session_id="")]
tool_execution> Tool:create_rpm_repository Args:{'domain': 'pulp-mcp-test', 'name': 'pulp-mcp-test-rpm-repo', 'remote': '', 'session_id': ''}
tool_execution> Tool:create_rpm_repository Response:[TextContentItem(text='{\n  "success": false,\n  "result": "Something is not right. Check it out: b\'{\\"name\\":[\\"This field must be unique.\\"]}\'"\n}', type='text')]

inference> The name 'pulp-mcp-test-rpm-repo' for the RPM repository cannot be created because it is not unique. The error message indicates that there might be another repository with this name in Pulp.

Please choose a different name for the repository.
```

-> Llama Stack (sends the result back to the LLM to format a nice response) -> Ollama (LLM generates a friendly answer) -> Llama Stack (sends it back to you in chat)!

Pretty neat, right? It's like having a little AI assistant dedicated to your Pulp instance.

---

### Configuring the AI Agent and its Tools

Setting up the communication between the LLM and the Pulp API was a crucial step. This involved defining how the AI agent would actually *use* the Pulp-specific tools I created. This script configures the agent, instructing it on how to interact with the `pulp::mcp` tools and manage the conversation flow.

```python
import uuid

from llama_stack_client import LlamaStackClient
from llama_stack_client.lib.agents.agent import Agent

from llama_stack_client.lib.agents.event_logger import EventLogger


base_url = "http://localhost:8321"
client = LlamaStackClient(base_url=base_url)
model = "llama3.2:3b-instruct-fp16"

instructions = """
You are a helpful assistant.
For anything related to pulp, check for functions from mcp::pulp tool.
You can interact with a pulp instance when using tools from mcp::pulp.
mcp::pulp doesn't need an session_id parameter.
You must not generate example code or scripts.
Don't generate usage examples. Use the tools available.
Don't simulate the output, perform all operations with tools available.
"""

# Register pulp tools
client.toolgroups.register(
    toolgroup_id="mcp::pulp",
    provider_id="model-context-protocol",
    mcp_endpoint={"uri": "http://localhost:8080/sse"}
)

agent = Agent(
    client,
    model=model,
    instructions=instructions,
    tools=["mcp::pulp"],
    enable_session_persistence=True,
    tool_config={
        "tool_choice": "required",
        "tool_prompt_format": "python_list"
    },
)

user_prompts = [
    # "Can you check the localhost pulp instance status?",
    "Can you retrieve all domains in Pulp?",
    "Can you create a new domain called pulp-mcp-test?",
    "Can you list all domains again?",
    "Can you list all rpm repositories for the domain we just created?",
    "Can you create a new rpm repository named 'pulp-mcp-test-rpm-repo' for the domain we just created?"
]

# Generate a new Unique Identifier for the session 
new_uuid = uuid.uuid4()
session_id = agent.create_session(f"mcp-session-{new_uuid}")

for prompt in user_prompts:

    print(f"\n{'='*100}\nProcessing user query: {prompt}\n{'='*100}")

    response = agent.create_turn(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        session_id=session_id
    )
    for log in EventLogger().log(response):
        log.print()

session_response = client.agents.session.retrieve(
    session_id=session_id,
    agent_id=agent.agent_id,
)
```

---

### The Real Talk: Hitting the Wall with Local LLMs

For this adventure, I mostly used the **`llama3.2:3b-instruct-fp16`** model running on Ollama. And, well, let's just say it was a humbling experience. The conversations weren't exactly mind-blowing. The LLM's responses were often a bit... off, or just not quite what you'd expect from a smart agent. It struggled to consistently nail the Pulp API calls correctly.

So, why the lukewarm results? Mostly, it boils down to a few key areas:

* **Hardware Constraints (for *bigger* models):** While my direct experiment was with a smaller model, it's worth noting that if I wanted to jump to a much larger, more capable LLM (like some of those top-tier ones on the benchmarks), my local hardware would immediately hit its limits. Running something like an 8B, 13B, or even 70B parameter model in full `fp16` demands serious GPU memory (VRAM) and raw processing power that just isn't common on a typical developer machine. These bigger models would simply crash or be painfully slow on my setup.

* **OpenAPI Tool Generation Hiccups:** My initial plan was pretty clever: use Pulp's own **OpenAPI definition schema**. FastMCP has this awesome feature where it can consume an OpenAPI spec and automatically generate MCP tools from all the routes defined within. This *should* have given the LLM direct access to every Pulp API endpoint as a callable tool.
    * However, for some reason, the `llama3.2:3b-instruct-fp16` model just **couldn't consistently recognize or properly call these automatically generated tools**. Instead of trying to use `create_repository` or `list_repositories`, it would keep generating examples of how to *ask* for things, or just ramble, completely missing the available tool.
    * This meant a pivot was needed. I ended up having to **manually write my own MCP tools** in Python. These custom tools would then internally make the appropriate calls to the Pulp API and carefully format the responses before sending them back to the LLM. It was a bit more work, but it ensured the LLM had well-defined, consumable functions it could actually invoke.

    ```python
    import base64

    import httpx

    from typing import TypedDict

    from fastmcp import FastMCP
    from fastmcp.server.openapi import RouteMap,MCPType


    auth = httpx.BasicAuth(username="admin", password="password")
    client = httpx.Client(base_url="http://localhost:5001", auth=auth)

    class Response(TypedDict):
        success: bool
        result: str

    mcp = FastMCP(name="Pulp MCP Server")

    @mcp.tool
    def get_pulp_status(session_id:str|None = None) -> Response:
        """Return the status of the pulp instance."""
        request = client.get("/pulp/api/v3/status/")
        try:
            request.raise_for_status()
            return {"success": True, "result": request.json()}
        except httpx.HTTPError as exc:
            return {"success": False, "result": str(exc)}

    @mcp.tool
    def get_pulp_domains(session_id:str|None = None) -> Response:
        """Return all pulp domains."""
        request = client.get("/pulp/default/api/v3/domains/")
        try:
            request.raise_for_status()
            return {"success": True, "result": request.json()}
        except httpx.HTTPError as exc:
            return {"success": False, "result": str(exc)}
        
    @mcp.tool
    def create_pulp_domain(name: str, labels:dict[str, str], session_id:str|None = None, description:str|None = None) -> Response:
        """Creates a new pulp domain."""
        domain = {}
        domain["name"] = name

        if description:
            domain["description"] = description

        if labels:
            domain["labels"] = labels

        domain["storage_class"] = "pulpcore.app.models.storage.FileSystem"

        domain["storage_settings"] = '{"media_root": "/var/lib/pulp/media/"}'

        request = client.post("/pulp/default/api/v3/domains/", json=domain)

        try:
            request.raise_for_status()
            return {"success": True, "result": request.json()}
        except httpx.HTTPError as exc:
            return {"success": False, "result": str(exc)}

    @mcp.tool
    def get_rpm_repositories(domain:str|None = None, session_id:str|None = None) -> Response:
        """Return all RPM repositories for a given domain."""
        request = client.get(f"/pulp/{domain}/api/v3/repositories/rpm/rpm/")
        try:
            request.raise_for_status()
            return {"success": True, "result": request.json()}
        except httpx.HTTPError as exc:
            return {"success": False, "result": str(exc)}


    @mcp.tool
    def create_rpm_repository(domain:str, name:str, remote:str|None, session_id:str|None = None, description:str|None = None) -> Response:
        """Create a new RPM Repository."""
        repository = {"name": name, "description":description}
        if not remote:
            repository["remote"] = None

        request = client.post(f"/pulp/{domain}/api/v3/repositories/rpm/rpm/", json=repository)

        if request.status_code == 201:
            return {"success": True, "result": request.json()}
        else:
            return {"success": False, "result": f"Something is not right. Check it out: {str(request.read())}"}
    ```

* **Context Window Limitations (the `3b` model's Achilles' Heel):** This was the *real* pain point for the `llama3.2:3b-instruct-fp16` model. It's not that my hardware couldn't *run* it, but this smaller model has a more limited **context window**. The context window is essentially the LLM's short-term memory – how much conversation (input *and* output tokens) it can "remember" at any given time.
    * When I'd feed it user requests, and then it needed to process potentially verbose responses directly from the Pulp API (think long JSON outputs or detailed error messages), that rapidly chewed up its context window.
    * Once the context window gets too full, the LLM starts "getting confused" and behaving in a strange way – its responses became incoherent, it lost track of the original request, or it would simply generate irrelevant text because the crucial context had literally scrolled out of its "mind." It was like trying to have a complex conversation with someone who has very short-term memory loss!
    * This is a common challenge with smaller models when dealing with detailed API interactions. The verbosity of API responses, even when trying to simplify them, can quickly overwhelm a limited context window.

* **Model Smarts (or Lack Thereof):** Even without context window issues, `llama3.2:3b-instruct-fp16` is a smaller sibling to larger, more powerful LLMs. It's a capable model for its size, but it's not designed to be a top-tier genius when it comes to intricate "tool calling" – which is what talking to the Pulp API really is. You need a truly smart model to figure out exactly which Pulp API endpoint to hit, what parameters it needs, and how to format the request just right, all from your natural language query. Smaller models generally have a tougher time with this kind of complex reasoning and precise instruction following.

* **The Pulp API Nuance:** Our Pulp API is powerful, but it has its own conventions and requires precision. A less capable LLM can easily get lost in the details, leading to incorrect calls or just plain confusion.

---

### The Silver Lining: Why This Was Still Awesome!

Even though our chat bot wasn't ready to replace Pulp's documentation just yet, this experiment was a massive win for a few key reasons:

* **Proof of Concept Achieved:** We *did it*! We successfully built an MCP server that connected to an LLM, and that LLM was wired up to try and talk to the Pulp API. This shows the fundamental plumbing works!
* **Local AI for Pulp FTW!:** Imagine super-specialized AI assistants for Pulp that live entirely on your own network. This setup is perfect for that, keeping everything private and secure.
* **Learning and Playing:** For anyone wanting to dive into LLMs and API interaction, this setup is a fantastic sandbox. No huge cloud bills, just pure experimentation!

---

### Where Do We Stack Up? (A Little Benchmark Peep)

If you're curious about how LLMs are judged on their "tool calling" abilities, check out the **[Berkeley Function Calling Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html)**. This leaderboard basically tests how well an LLM can understand what you want it to *do* (like "list all repos") and then correctly translate that into an API call.

You'll quickly see that the top contenders on that list are typically huge, powerful models that gobble up resources. My little `llama3.2:3b-instruct-fp16`, while valiant, isn't playing in the same league as those giants when it comes to complex API interactions. This just reinforces that achieving truly intelligent API interaction, especially with a model of this size, requires clever strategies to manage that precious context window and potentially more robust models to unlock its full potential.

---

### Wrapping Up

So, while my little Pulp-chatting AI isn't ready for prime time (yet!), this journey of building an MCP server, wiring it to Pulp through an LLM, was incredibly insightful. It proves that the framework is there. As LLMs get more efficient, context windows expand, and hardware becomes even more powerful and affordable, I truly believe we'll see some incredibly smart, privacy-first AI agents helping us manage our Pulp instances.

This is just the beginning, team! What kind of Pulp-powered AI dreams are *you* cooking up?
