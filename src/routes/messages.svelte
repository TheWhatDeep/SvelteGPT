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
</script>
<style>

</style>

<section class="messages">
    {#await receiveMessages("Who am I?") }
        <p>...waiting</p>
    {:then number}
        <p>{ number }</p>
    {:catch error}
        <p style="color: red">{error.message}</p>
    {/await}
</section>