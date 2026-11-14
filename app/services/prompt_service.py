from typing import Optional

class PromptService:
    @staticmethod
    def enhance_prompt(
        user_prompt: str,
        room_type: Optional[str] = "Living Room",
        style: Optional[str] = "Modern",
        primary_color: Optional[str] = None,
        secondary_color: Optional[str] = None,
        accent_color: Optional[str] = None,
        room_analysis: Optional[dict] = None,
    ) -> str:
        """
        Converts user preferences and color palette into a structured,
        photorealistic interior design generation prompt.
        """
        color_details = []
        if primary_color:
            color_details.append(f"primary tone {primary_color}")
        if secondary_color:
            color_details.append(f"secondary tone {secondary_color}")
        if accent_color:
            color_details.append(f"accent color {accent_color}")
                
        color_string = f" with a curated color palette of {', '.join(color_details)}" if color_details else ""

        analysis_details = ""
        if room_analysis:
            furniture = room_analysis.get("furniture")
            layout_notes = room_analysis.get("layout_notes")
            if furniture:
                analysis_details += f" Preserve the room's existing furniture: {', '.join(furniture)}."
            if layout_notes:
                analysis_details += f" Preserve its spatial layout: {layout_notes}."

        enhanced = (
            f"Professional interior design photograph of a {(room_type or 'room').lower()},"
            f"executed in a {(style or 'balanced').lower()} design style{color_string}."
            f"Feature architectural lighting, high-end materials, realistic textures,"
            f"and clean spatial composition.{analysis_details} Specific user request: {user_prompt}."
        )
        return enhanced
                