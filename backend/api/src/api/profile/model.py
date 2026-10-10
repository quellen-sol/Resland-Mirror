from pydantic import BaseModel


# The base profile as stored, ids included, so a client that writes its own
# tailored resume (the personal MCP server) can point back at experiences.
# Same rows and order the tailor agent reads.
class ProfileBullet(BaseModel):
    id: int
    text: str


class ProfileExperience(BaseModel):
    id: int
    company_name: str
    title: str
    start_date: str
    end_date: str | None = None
    description: str | None = None
    bullets: list[ProfileBullet]


class ProfileSkill(BaseModel):
    name: str
    category: str | None = None


class ProfileEducation(BaseModel):
    institution: str
    degree: str
    field_of_study: str
    start_date: str
    end_date: str | None = None
    description: str | None = None


class ProfileProject(BaseModel):
    name: str
    link: str | None = None
    description: str | None = None
    start_date: str
    end_date: str | None = None


class ProfileSocialLink(BaseModel):
    type: str
    link: str


class ProfileResponse(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    summary: str | None = None
    social_links: list[ProfileSocialLink]
    experiences: list[ProfileExperience]
    # Display order; a category's skills form one contiguous run.
    skills: list[ProfileSkill]
    education: list[ProfileEducation]
    projects: list[ProfileProject]
