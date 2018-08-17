# -*- encoding:utf8 -*-

from collections import defaultdict, namedtuple, Counter
import math
from hanziminer import Corpus, Tools


class TokenExtractor:

    _score_header = ['freq', 'cohesion_l', 'cohesion_r', 'cohesion', 'cohesion_s', 'branch_entropy_l', 'branch_entropy_r', 'branch_entropy' ]

    def __init__( self, corpus ):
        self.corpus = corpus
        self.token_counter = Counter()
        self.unigram_counter = Counter( self.corpus.to_string() )
        self.bigram_counter = Counter()

    def _cohesion_score( self, word ):
        word_len = len( word )
        if (not word) or ( word_len < self.min_window ):
            return 0

        first_chr_freq = self.unigram_counter[ word[0] ]
        last_chr_freq = self.unigram_counter[ word[-1] ]
        whole_word_freq = self.token_counter[ word ]

        cohesion_l = 0 if whole_word_freq == 0 else math.pow( ( whole_word_freq / first_chr_freq ), (1 / (word_len - 1)) )
        cohesion_r = 0 if whole_word_freq == 0 else math.pow( ( whole_word_freq / last_chr_freq ), (1 / (word_len - 1)) )
        cohesion = math.sqrt(cohesion_l * cohesion_r)
        return ( cohesion_l, cohesion_r, cohesion , (cohesion_l + cohesion_r)/2 )

    def _branch_entropy_score( self, word ):
        word_len = len( word )
        whole_word_freq = self.token_counter[ word ]
        token_l, token_r = word[:-1], word[1:]
        branch_entropy_l = self.__class__.entropy( whole_word_freq / self.token_counter[token_l] ) if ( token_l in self.token_counter ) and (self.token_counter[token_l] != 0 ) else 0
        branch_entropy_r = self.__class__.entropy( whole_word_freq / self.token_counter[token_r] ) if ( token_r in self.token_counter ) and (self.token_counter[token_r] != 0 ) else 0

        # debuging ###
        if not( ( token_l in self.token_counter ) and (self.token_counter[token_l] != 0 ) ):
            print("token_l", word, token_l, self.token_counter[token_l] )

        if not ( ( token_r in self.token_counter ) and (self.token_counter[token_r] != 0 ) ):
            print("token_r", word, token_r, self.token_counter[token_r] )
        ###

        return ( ( token_l, branch_entropy_l ), ( token_r, branch_entropy_r ) )

   # return self

    def train( self, min_freq = 5, min_window=2, max_window=8  ):
        self.min_freq = min_freq
        self.max_window = max_window
        if min_window < 2:
            self.min_window = 2
            print("!!! Min_window must be greater than 2. Automatically set 2")
        else:
            self.min_window = min_window

        corpus_size = len( self.corpus.to_list() )

        print("# Training ... ")
        for i, doc in enumerate( self.corpus.to_list() ):
            Tools.print_progress(i+1, corpus_size, prefix='Progress', suffix='Complete')
            for phrase in doc:
                particles = Corpus.allgram( phrase, min_window- 1 , max_window + 1 ) # branch entropy를 구히기 위해 window 범위를 1씩 늘림
                self.token_counter.update( Counter( particles ) )

                bigrams = Corpus.ngram( phrase, n=2 )
                self.bigram_counter.update( Counter( bigrams ) )

        # Branch Entropy
        self._total_branch_entropy_score()
        print( "# Training was done. Used memory {:.3f} Gb".format( Tools.get_process_memory() ) )
        return self

    def _total_branch_entropy_score( self ):
        branch_entropy_l = defaultdict(lambda: 0)
        branch_entropy_r = defaultdict(lambda: 0)
        for (w, f) in self.token_counter.items():
            if ( len(w) < self.min_window ): continue
            be_l, be_r = self._branch_entropy_score( w )
            branch_entropy_l[ be_l[0] ] += be_l[1]
            branch_entropy_r[ be_r[0] ] += be_r[1]
        self.total_branch_entropy_l = branch_entropy_l
        self.total_branch_entropy_r = branch_entropy_r
        return self

    def score_header(self):
        return self._score_header

    def extract( self ):
        self._score = defaultdict()
        _score = namedtuple('Score', self._score_header )
        self._token_counter_gt = { k: self.token_counter[k] for k in self.token_counter
            if ( ( len(k) - self.max_window ) * ( len(k) - self.min_window ) <= 0 ) and self.token_counter[k] >= self.min_freq }

        i = 0
        total_len = len( self._token_counter_gt )
        print("\r# Extracting ..." )
        for (w, f) in self._token_counter_gt.items():

            _freq = f
            # Cohesion Score
            _cohesion_l, _cohesion_r, _cohesion, _cohesion_s  = self._cohesion_score( w )
            # Branch Entropy Score
            _branch_entropy_l = self.total_branch_entropy_l[w]
            _branch_entropy_r = self.total_branch_entropy_r[w]
            _branch_entropy = ( _branch_entropy_l + _branch_entropy_r ) / 2
            self._score[ w ] = _score( _freq, _cohesion_l, _cohesion_r, _cohesion, _cohesion_s, _branch_entropy_l, _branch_entropy_r, _branch_entropy )

            # Report progress
            Tools.print_progress(i+1, total_len, prefix='Progress', suffix='Complete')
            i += 1

        print("# Extrating was done. System memory {:.3f} Gb used".format( Tools.get_process_memory()) )
        return self

    # get score
    def score(self):
        return self._score

    def report(self, output_filename, sep="\t", order="cohesion"):
        handler = open(output_filename, 'w', encoding="utf-8")
        header = "token" + sep + sep.join( self._score_header ) + "\n"
        handler.write(header)

        _score_list = self.score().items()
        score_list = sorted( _score_list, key=lambda x: getattr( x[1], order ), reverse=True )
        for word, score in score_list:
            handler.write( word + sep + sep.join( [ "{:01.3f}".format( getattr( score, s ) ) for s in self._score_header ]) + "\n" )
        handler.close()
        print("# {:d} of tokens were reported in {}".format( len( score_list) , output_filename  ) )

    @staticmethod
    def entropy( p ):
        return -1 * p * math.log2( p )
