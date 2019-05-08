<template>
<v-container grid-list-md text-align-center
> 
  <v-layout pa-2 ma-4 row wrap>
    <v-flex md12 class="font-weight-thin display-2">
      <span>Semantic Classification of Questions on Q&A Websites</span>
    </v-flex>
  </v-layout>
  <v-layout row wrap>
    <v-flex md12>
      <v-text-field
      label="Type a question"
      v-model="userInput"
      clearable
      :disabled="disableUI"
      @keypress.enter="submitQuery()"
      ></v-text-field>
    </v-flex>
    <v-flex data-app>
      <v-combobox
      v-model="setDataset"
      :items="datasets"
      :loading="disableUI"
      :disabled="disableUI"
      @change="changeDataset()">
      </v-combobox>
    </v-flex>
    <v-spacer></v-spacer>
    <v-flex>
      <v-btn
      type="button"
      large
      right
      round
      dark
      class="mx-3"
      @click="submitQuery()"
      :disabled="disableUI"
      >Submit</v-btn>
    </v-flex>
  </v-layout>
  <v-layout>
    <v-snackbar
    v-model="snackbar"
    bottom
    :timeout="3000"
    ><span class="subheading">Set labeling model to use {{ setDataset }}</span>
    </v-snackbar>
  </v-layout>
</v-container>
</template>

<script>
import axios from 'axios'

export default {
  name: 'home',
  data() {
    return {
      userInput: '',
      setDataset: table,
      datasets: ['TREC', 'Photography', 'Compiled'],
      disableUI: false,
      snackbar: false
    }
  },
  methods: {
    submitQuery() {
      if(this.userInput !== '')
        this.$router.push({ path: '/results', query: { q: this.userInput }})
    },
    changeDataset() {
      this.disableUI = true
      axios({
        method: 'GET',
        url: '/set_dataset/',
        params: {
          dataset: this.setDataset
        }
      })
        .then(() => {
          this.disableUI = false
          this.snackbar = true
          table = this.setDataset
        })
    }
  }
}
</script>
