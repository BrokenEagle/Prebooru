# APP/MODELS/IMAGE_HASH.PY

# ## LOCAL IMPORTS
from .base import JsonModel, integer_column, real_column, blob_column

# ## GLOBAL VARIABLES

# #### Constants

BITS_PER_BYTE = 8


# #### Configurable

HASH_SIZE = 16            # Must be a power of 2
BYTES_PER_CHUNK = 1       # Must be a power of 2 or the value 1


# #### Calculated

BITS_PER_CHUNK = BYTES_PER_CHUNK * BITS_PER_BYTE
NUM_CHUNKS = (HASH_SIZE * HASH_SIZE) // BITS_PER_CHUNK
TOTAL_BITS = HASH_SIZE * HASH_SIZE


# ## FUNCTIONS

def chunk_key(index):
    return 'chunk' + str(index).zfill(2)


def chunk_index(index):
    return index * BYTES_PER_CHUNK


def hex_chunk(hashstr, index):
    strindex = chunk_index(index)
    return hashstr[strindex: strindex + BYTES_PER_CHUNK]


# ## CLASSES

class ImageHash(JsonModel):
    # ## Columns
    id = integer_column(primary_key=True)
    post_id = integer_column(foreign_key='post.id', nullable=False, index=True)
    ratio = real_column(nullable=False)

    # ## Relations
    # (OtO) post [Post]

    # ## Instance properties

    @property
    def hash(self):
        rethash = b""
        for i in range(0, NUM_CHUNKS):
            temp = getattr(self, chunk_key(i))
            if temp is None:
                return None
            rethash += temp
        return rethash

    @hash.setter
    def hash(self, image_hash):
        for i in range(0, NUM_CHUNKS):
            setattr(self, chunk_key(i), hex_chunk(image_hash, i))

    # ## Class properties

    @classmethod
    def ratio_clause(cls, ratio):
        ratio_low = round(ratio * 99, 4) / 100
        ratio_high = round(ratio * 101, 4) / 100
        return cls.ratio.between(ratio_low, ratio_high)

    @classmethod
    def chunk_similarity_clause(cls, image_hash):
        clause = cls.chunk00 == image_hash[0:2]
        for i in range(1, NUM_CHUNKS):
            clause |= (getattr(cls, chunk_key(i)) == hex_chunk(image_hash, i))
        return clause

    @classmethod
    def cross_similarity_clause0(cls, image_hash):
        clause = None
        for i in range(NUM_CHUNKS):
            # XXXX  Left-Right
            #
            # ##XX  Backward-Down
            # XX##
            chunk1 = i
            chunk2 = (i + 1) % NUM_CHUNKS
            subclause = (getattr(cls, chunk_key(chunk1)) == hex_chunk(image_hash, chunk1)) &\
                        (getattr(cls, chunk_key(chunk2)) == hex_chunk(image_hash, chunk2))
            groupclause = subclause.self_group()
            clause = clause | groupclause if clause is not None else groupclause
        return clause

    @classmethod
    def cross_similarity_clause1(cls, image_hash):
        clause = None
        for i in range(NUM_CHUNKS):
            # XXXX  Left-Right
            #
            # ##XX  Backward-Down
            # XX##
            chunk1 = i
            chunk2 = (i + 1) % NUM_CHUNKS
            subclause = (getattr(cls, chunk_key(chunk1)) == hex_chunk(image_hash, chunk1)) &\
                        (getattr(cls, chunk_key(chunk2)) == hex_chunk(image_hash, chunk2))
            groupclause = subclause.self_group()
            clause = clause | groupclause if clause is not None else groupclause
        for i in range(NUM_CHUNKS // 2):
            # XX##  Forward-Down
            # ##XX
            chunk1 = i * 2
            chunk2 = (chunk1 + 3) % NUM_CHUNKS
            subclause = (getattr(cls, chunk_key(chunk1)) == hex_chunk(image_hash, chunk1)) &\
                        (getattr(cls, chunk_key(chunk2)) == hex_chunk(image_hash, chunk2))
            groupclause = subclause.self_group()
            clause |= groupclause
        return clause

    @classmethod
    def cross_similarity_clause2(cls, image_hash):
        clause = None
        for i in range(NUM_CHUNKS):
            # XX##  Rightwards zag
            # ##XX
            # XX##
            if i % 2 == 0:
                chunk1 = i
                chunk2 = (i + 3) % NUM_CHUNKS
                chunk3 = (i + 4) % NUM_CHUNKS
            # ##XX  Leftwards zag
            # XX##
            # ##XX
            else:
                chunk1 = i
                chunk2 = (i + 1) % NUM_CHUNKS
                chunk3 = (i + 4) % NUM_CHUNKS
            subclause = (getattr(cls, chunk_key(chunk1)) == hex_chunk(image_hash, chunk1)) &\
                        (getattr(cls, chunk_key(chunk2)) == hex_chunk(image_hash, chunk2)) &\
                        (getattr(cls, chunk_key(chunk3)) == hex_chunk(image_hash, chunk3))
            groupclause = subclause.self_group()
            clause = clause | groupclause if clause is not None else groupclause
        return clause

    basic_attributes = ['id', 'post_id', 'ratio']
    json_attributes = basic_attributes + ['hash']
    repr_attributes = json_attributes


# ## INITIALIZATION

def initialize():
    # Initialize chunk attributes, CHUNK00 - CHUNKXX
    for i in range(0, NUM_CHUNKS):
        key = chunk_key(i)
        setattr(ImageHash, key, blob_column(nullable=False))
