<script>
    import './style.css';
    import Messages from './messages.svelte'
</script>
<main>
    <aside></aside>
    <div id="app">
        <nav class="navbar">
            <button type="button" class="nav-link">
                <img src="/menu.svg" alt="menu">
            </button>
            <button type="button" class="nav-link" style="margin-left: auto;">
                <img src="/settings.svg" alt="user">
            </button>
        </nav>
        <Messages>
        </Messages>
    </div>
</main>