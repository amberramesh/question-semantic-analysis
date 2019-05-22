<template>
<v-app>
  <v-container> 
    <v-layout pa-2 ma-4 row wrap>
      <v-flex md12 class="text-md-center font-weight-thin display-2">
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
        box
        @keypress.enter="submitQuery()"
        ></v-text-field>
      </v-flex>
    </v-layout>
    <v-layout row wrap justify-center>
      <v-spacer></v-spacer>
      <v-flex ma-2 md2 class="form-label font-weight-thin title">
        <span>Labeling Dataset</span>
      </v-flex>
      <v-flex ma-2 md6 data-app>
        <v-combobox
        v-model="setDataset"
        :items="datasets"
        :loading="disableUI"
        :disabled="disableUI"
        hint="Changes the dataset used for applying tags"
        persistent-hint
        @change="changeDataset()">
        </v-combobox>
      </v-flex>
      <v-spacer></v-spacer>
    </v-layout>
    <v-layout row wrap justify-center>
      <v-spacer></v-spacer>
      <v-flex ma-2 md2 class="form-label font-weight-thin title">
        <span>Fetch Size</span>
      </v-flex>
      <v-flex ma-2 md6 data-app>
        <v-combobox
        v-model="setFetchSize"
        :items="fetchSizes"
        :disabled="disableUI"
        hint="Number of similar questions to be retrieved"
        persistent-hint>
        </v-combobox>
      </v-flex>
      <v-spacer></v-spacer>
    </v-layout>
    <v-layout my-4 wrap style justify-center>
      <div>
      <v-btn
      type="button"
      large
      round
      dark
      class="mx-3"
      @click="submitQuery()"
      :disabled="disableUI"
      >Submit</v-btn>
      </div>
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
</v-app>
</template>

<style>
.form-label {
  align-self: center;
  text-align: right
}

</style>

<script>
import axios from 'axios'

export const datasetDict = {
  'TREC': 'trec',
  'Photography': 'photography',
  'Compiled': 'compiled'
}

export default {
  name: 'home',
  data() {
    return {
      userInput: '',
      setDataset: table,
      setFetchSize: 25,
      datasets: ['TREC', 'Photography', 'Compiled'],
      fetchSizes: [10, 25, 50],
      disableUI: false,
      snackbar: false
    }
  },
  methods: {
    submitQuery() {
      if(this.userInput !== '')
        this.$router.push({ path: '/results', query: { q: this.userInput, fetchSize: this.setFetchSize }})
    },
    changeDataset() {
      this.disableUI = true
      axios({
        method: 'GET',
        url: '/set_dataset/',
        params: {
          dataset: datasetDict[this.setDataset]
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
