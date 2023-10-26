
class TimeDefinition(BaseModel):
    years: Union[str,List[int]]



    @classmethod
    def from_simplicity(cls, root_dir):
        