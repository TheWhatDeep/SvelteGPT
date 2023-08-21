<script>
    import { ChatOpenAI } from "langchain/chat_models/openai";
    import { HumanMessage, ChatMessage, SystemMessage } from "langchain/schema";

    const chat = new ChatOpenAI({
        temperature: 0,
        openAIApiKey: "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"
    });

    async function receiveMessages(message) {
        const result = await chat.predict(message);
        return result;
    }

    function getInput() {

    }

</script>

<section class="messages">
    {#await receiveMessages("Who am I?") }
        <p>...waiting</p>
    {:then number}
        <p>{ number }</p>
    {:catch error}
        <p style="color: red">{error.message}</p>
    {/await}
</section>
<div class="chatbox">
    <input type="text" name="message" id="message">
</div>