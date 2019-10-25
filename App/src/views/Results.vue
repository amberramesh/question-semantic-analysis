<template>
  <v-app>
    <v-container grid-list-md text-md-center>
      <v-layout pa-3 mb-2 row wrap>
        <v-flex md12 class="subheading">You asked</v-flex>
        <v-flex md12 class="font-weight-medium display-2"><span>{{ $route.query.q }}</span></v-flex>
        <v-layout v-if="showLabels" row wrap>
          <v-flex md12 mt-2 class="subheading">Tags identified for this question</v-flex>
          <v-flex md12>
            <v-chip
            label
            :key="index" v-for="(tag, index) in tags"
            :dark="index % 2 === 0"
            class="subheading pa-1"
            ><v-avatar
            tile
            class="grey"
            :class="{ 'darken-2': index % 2 === 0, 'lighten-3': index % 2 !== 0}"
            ><span class="pa-1">{{ tag.value }}</span></v-avatar>
            <span class="px-2">{{ tag.key }}</span></v-chip>
          </v-flex>
        </v-layout>
        <v-layout v-else pa-5 mb-2 row wrap align-content-center>
          <v-flex md12 class="subheading">Computing label probabilities</v-flex>
          <v-flex md12 ma-2>
            <v-progress-circular indeterminate></v-progress-circular>
          </v-flex>
        </v-layout>
      </v-layout>

      <v-layout v-if="showContext" pa-3 mb-2 row wrap>
        <v-layout v-if="testDuplicates" pb-3 my-1 row wrap align-content-center>
          <v-flex md12 class="subheading">{{ duplicateText }}
            <v-badge
            v-if="duplicates.length > 0"
            color="red"
            class="ma-2">
            <template v-slot:badge>
              <span>D</span>
            </template></v-badge>
          </v-flex>
          <v-flex v-if="!tasksComplete" md12 ma-2>
            <v-progress-circular indeterminate></v-progress-circular>
          </v-flex>
        </v-layout>
        <v-flex md12>
          <v-card>
            <v-card-title class="title mx-3"><h4>Questions similar to yours</h4></v-card-title>
            <v-list>
              <template v-for="(question, index) in pagedQuestions">
                <v-divider :key="'d' + ((pageNumber - 1) * 5 + index)"></v-divider>
                <v-list-tile :key="'t' + ((pageNumber - 1) * 5 + index)">
                    <v-badge
                    v-model="duplicateDict[(pageNumber - 1) * 5 + index]"
                    color="red"
                    left
                    overlap>
                      <template v-slot:badge>
                        <span>D</span>
                      </template><v-list-tile-content>
                    <v-list-tile-title class="mx-4">
                      <span class="font-weight-regular title">
                        {{ question.slice(0, (question.length > 100) ? 100 : question.length).concat(question.length > 100 ? '...' : '') }}
                      </span>
                    </v-list-tile-title>
                  </v-list-tile-content>
                    </v-badge>
                </v-list-tile>
              </template>
            </v-list>
          </v-card>
        </v-flex>
        <v-flex md12>
          <v-pagination
          v-model="pageNumber"
          :length="Math.ceil(similarQuestions.length/5)"
          light
          class="ma-2"
          ></v-pagination>
        </v-flex>
      </v-layout>
      <v-layout v-else pa-5 mb-2 row wrap align-content-center>
        <v-flex md12 class="subheading">{{ contextText }}</v-flex>
        <v-flex md12 ma-2>
          <v-progress-circular indeterminate></v-progress-circular>
        </v-flex>
      </v-layout>
    </v-container>
  </v-app>
</template>

<script>
const axios = require('axios')

export default {
  name: 'results',
  data() {
    return {
      showLabels: false,
      showContext: false,
      testDuplicates: false,
      tasksComplete: false,
      contextText: 'Waiting for label classifier to finish',
      duplicateText: 'Searching for duplicates',
      pageNumber: 1,
      colors: ['deep-purple', 'pink', 'blue', 'cyan', 'red', 'teal', 'brown', 'light-green'],
      tags: [],
      similarQuestions: [],
      duplicates: []
    }
  },
  computed: {
    pagedQuestions() {
      let questions = []
      let offset = (this.pageNumber - 1) * 5
      for(let i = 0 + offset; i < this.similarQuestions.length && i < (5 + offset); i++)
        questions.push(this.similarQuestions[i])
      return questions
    },
    duplicateDict() {
      let dict = {}
      this.similarQuestions.forEach( (s, i) => {
        dict[i] = false
      })
      this.duplicates.forEach( d => {
        let pos = this.similarQuestions.indexOf(d)
        dict[pos] = true
      })
      return dict
    }
  },
  methods: {
    getRandomInt(index) {
      return (Math.floor(Math.random() * Math.floor(3)) * 2 + (index % 2))
    }
  },
  mounted() {
    if(this.$route.query.q === undefined || this.$route.query.q === '')
      this.$router.push('/')

    axios({
      method: 'GET',
      url: '/Semantics/Labels',
      params: {
        q: this.$route.query.q
      }
    })
      .then(res => {
        // console.log(res.data)
        // GET request for similar questions
        const data = res.data
        let keys = Object.keys(data)
        let tags = []
        keys.forEach(key => {
          tags.push({ key: key, value: data[key] })
        })
        this.tags = tags
        this.showLabels = true
        this.contextText = 'Retrieving similar questions'
        axios(
          {
            method: 'GET',
            url: '/Semantics/Similarity',
            params: {
              q: this.$route.query.q,
              fetchSize: this.$route.query.fetchSize
            }
          }
        )
          .then(res => {
            const data = res.data
            // console.log(data)
            this.similarQuestions = data
            this.showContext = true
            this.testDuplicates = true

            // GET request for identifying duplicates
            axios({
              method: 'GET',
              url: '/Semantics/Duplicates',
              params: {
                q: this.$route.query.q
              }
            })
              .then(res => {
                const data = res.data
                // console.log(data)
                this.duplicates = data
                this.tasksComplete = true
                if(this.duplicates.length > 0)
                  this.duplicateText = 'Close matches were found for your question. Look for questions marked with'
                else
                  this.duplicateText = 'No close matches found for your question.'
              })
          })
      })
  }
}
</script>

<style scoped>

.v-list__tile__title .headline {
  line-height: unset !important
}

</style>


