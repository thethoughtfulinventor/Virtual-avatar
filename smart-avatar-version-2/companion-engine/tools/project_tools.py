from tools.base_tool import BaseTool


class ProjectLookupTool(BaseTool):
    """
    Gets the status and details of one project
    by name.

    Use when the user asks specifically about
    a named project's progress or status.
    """

    name = "project_lookup"
    description = (
        "Gets the status and details of a "
        "specific project by name. Use when "
        "the user asks about a particular "
        "project's status or progress."
    )

    def run(self, args, context):

        memory = context.get("memory")

        if not memory:
            return "Memory system unavailable."

        name = args.get("name", "").strip()

        if not name:
            return "No project name provided."

        project = memory.get_project(name)

        if not project:
            return f"No project found named '{name}'."

        status = project.get("status", "unknown")

        updated = (
            project
            .get("last_updated", "unknown")[:10]
        )

        return (
            f"{name}: "
            f"status={status}, "
            f"last updated={updated}"
        )


class ProjectsListTool(BaseTool):
    """
    Lists all tracked projects.

    Use when the user asks about their
    projects in general, or wants an overview
    of what's being tracked.
    """

    name = "projects_list"
    description = (
        "Lists all active tracked projects and "
        "their statuses. Use when the user asks "
        "about their projects in general."
    )

    def run(self, args, context):

        memory = context.get("memory")

        if not memory:
            return "Memory system unavailable."

        names = memory.list_projects()

        if not names:
            return "No projects are currently tracked."

        lines = []

        for name in names:

            project = memory.get_project(name)

            if project:
                status = project.get(
                    "status", "unknown"
                )
                lines.append(
                    f"- {name} ({status})"
                )

        return "\n".join(lines)