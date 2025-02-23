<script lang="ts">
  import type { UploadedImage, SortType } from "$lib/types";

  export let images: UploadedImage[] = [];
  export let letClose: boolean = false;
  export let closeHandler: (name: string) => void = (_) => {}
  export let expandHandler: (name: string) => void = (_) => {}
  export let sortType: SortType = 'None';

  let shallowImages = [...images];

  function sortByNameAsc(fst: UploadedImage, snd: UploadedImage) {
    if (fst.name < snd.name) return -1;
    if (fst.name > snd.name) return 1;
    return 0;
  }

  function sortByNameDesc(fst: UploadedImage, snd: UploadedImage) {
    return -1 * sortByNameAsc(fst, snd);
  }

  function sortByImportanceAsc(fst: UploadedImage, snd: UploadedImage) {
    const pred1 = fst?.inferenceResponse?.prediction?.target
    const pred2 = snd?.inferenceResponse?.prediction?.target
    if (pred1 && !pred2) return 1;
    if (pred2 && !pred1) return -1;
    return 0;
  }

  function sortByImportanceDesc(fst: UploadedImage, snd: UploadedImage) {
    return -1 * sortByImportanceAsc(fst, snd);
  }

  // Wait for changes of sortype
  $: {
    shallowImages = [...images]
    if (sortType === 'NameAsc') {
      shallowImages.sort(sortByNameAsc);
    }
    else if (sortType === 'NameDesc') {
      shallowImages.sort(sortByNameDesc);
    }
    else if (sortType === 'ImportanceAsc') {
        shallowImages.sort(sortByImportanceAsc);
    }
    else if (sortType === 'ImportanceDesc') {
        shallowImages.sort(sortByImportanceDesc);
    }
    shallowImages = [...shallowImages];
  }


</script>

<div class="container">
  <div class="img-grid">
    {#each shallowImages as img}
      <div id={img.name}
           class="img-container"
           class:melanoma={img.inferenceResponse && img?.inferenceResponse?.prediction?.target}
           class:not-melanoma={img.inferenceResponse && !img?.inferenceResponse?.prediction?.target}>
        <img src={img.url} alt="whatever" />
        <!-- svelte-ignore a11y-click-events-have-key-events -->
        {#if letClose}
          <div class="interactive-btn-img"
               on:click={() => closeHandler(img.name)}>
            <span class="material-icons">
            close
            </span>
          </div>
        {/if}
        <!-- svelte-ignore a11y-click-events-have-key-events -->
        {#if img.inferenceResponse}
          <div class="interactive-btn-img"
               on:click={() => expandHandler(img.name)}>
            <span class="material-icons">
            fullscreen
            </span>
          </div>
        {/if}
      </div>
    {/each}
  </div>
</div>

<style>
  .container {
    background: #eee;
    border: 1px solid #ccc;
    border-radius: 0.25rem;
    padding: 0.75rem;
  }

  .melanoma {
    background-color: rgba(255, 99, 132) !important;
  }

  .not-melanoma {
    background-color: #5ba0ce !important;
  }

  .img-container {
    position: relative;
    padding: 3px;
    background-color: transparent;
    border-radius: 2px;
  }

  /* make images fill their container*/
  img {
    object-fit: cover;
    width: 100%;
    height: 100%;
  }

  /* CSS Grid*/
  .img-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    grid-gap: 10px;
  }

  .interactive-btn-img {
    width: 21px;
    height: 21px;
    position: absolute;
    top: 10px;
    right: 10px;
    z-index: 1;
    border-radius: 50%;
    line-height: 24px;
    z-index: 1;
    cursor: pointer;
    background-color: black;
    color: white;
    text-align: center;
    opacity: 0.6;
  }

  .interactive-btn-img span {
    font-size: 21px;
  }

</style>
